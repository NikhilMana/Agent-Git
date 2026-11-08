import json
import hashlib
import uuid
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from backend.app.models.repository import Repository
from backend.app.models.branch import Branch
from backend.app.models.commit import Commit
from backend.app.models.snapshot import SnapshotItem
from backend.app.models.memory import MemoryItem
from backend.app.schemas.memory import MemoryItemCreate
from backend.app.schemas.commit import CommitCreate, CommitDiffResponse, SnapshotItemResponse
from backend.app.schemas.merge import MergeConflictDetail
from backend.app.services.audit_service import AuditService
from backend.app.core.logging import logger


def compute_snapshot_hash(items: List[Dict[str, Any]]) -> str:
    """Compute canonical SHA-256 hash of a snapshot's items."""
    canonical_items = []
    for item in items:
        # Normalize fields
        src_ids = sorted(item.get("source_message_ids") or [])
        canonical_item = {
            "logical_key": item.get("logical_key") or "",
            "content": (item.get("content_at_commit") or item.get("content") or "").strip(),
            "category": item.get("category_at_commit") or item.get("category") or "",
            "topic": item.get("topic_at_commit") or item.get("topic") or "",
            "source_message_ids": src_ids,
            "retention_action": item.get("retention_action_at_commit") or item.get("retention_action") or "retain"
        }
        canonical_items.append(canonical_item)

    # Sort deterministically by logical_key, then content
    canonical_items.sort(key=lambda x: (x["logical_key"], x["content"]))

    serialized = json.dumps(canonical_items, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class VersionService:
    def __init__(self, db: Session):
        self.db = db
        self.audit = AuditService(db)

    # Repository management
    def get_repository_by_id_or_name(self, identifier: str) -> Optional[Repository]:
        # Check by ID first
        stmt = select(Repository).where(Repository.id == identifier)
        repo = self.db.scalars(stmt).first()
        if repo:
            return repo
        # Check by Name
        stmt = select(Repository).where(Repository.name == identifier)
        return self.db.scalars(stmt).first()

    def get_or_create_repository(
        self,
        name: str = "default",
        description: Optional[str] = None,
        identifier: Optional[str] = None
    ) -> Repository:
        target = identifier or name
        repo = self.get_repository_by_id_or_name(target)
        if not repo:
            repo_id = str(uuid.uuid4())
            repo = Repository(
                id=repo_id,
                name=target,
                description=description or f"AgentGit Repository: {target}",
                default_branch="main"
            )
            self.db.add(repo)
            self.db.flush()

            # Create default main branch
            main_branch = Branch(
                id=str(uuid.uuid4()),
                repository_id=repo.id,
                name="main",
                head_commit_id=None,
                created_from_commit_id=None
            )
            self.db.add(main_branch)
            self.db.commit()
            self.db.refresh(repo)
            self.audit.record_event("repository_create", entity_id=repo.id, payload={"name": target})
        return repo

    def get_repository(self, repo_id: str) -> Optional[Repository]:
        return self.get_repository_by_id_or_name(repo_id)

    def list_repositories(self) -> List[Repository]:
        stmt = select(Repository).order_by(Repository.created_at.desc())
        return list(self.db.scalars(stmt).all())

    # Branch management
    def get_branch(self, repository_id: str, branch_name: str) -> Optional[Branch]:
        repo = self.get_repository(repository_id)
        target_id = repo.id if repo else repository_id
        stmt = select(Branch).where(
            Branch.repository_id == target_id,
            Branch.name == branch_name
        )
        return self.db.scalars(stmt).first()

    def list_branches(self, repository_id: str) -> List[Branch]:
        repo = self.get_repository(repository_id)
        target_id = repo.id if repo else repository_id
        stmt = select(Branch).where(Branch.repository_id == target_id).order_by(Branch.created_at.asc())
        return list(self.db.scalars(stmt).all())

    def create_branch(self, repository_id: str, name: str, from_commit_id: Optional[str] = None) -> Branch:
        repo = self.get_repository(repository_id)
        if not repo:
            raise ValueError(f"Repository '{repository_id}' not found.")

        existing = self.get_branch(repository_id, name)
        if existing:
            raise ValueError(f"Branch '{name}' already exists in repository.")

        # If from_commit_id is not specified, use repository default branch head
        head_commit_id = from_commit_id
        if not head_commit_id:
            default_b = self.get_branch(repository_id, repo.default_branch)
            if default_b:
                head_commit_id = default_b.head_commit_id

        if head_commit_id:
            commit = self.get_commit(head_commit_id)
            if not commit:
                raise ValueError(f"Starting commit '{head_commit_id}' not found.")

        branch = Branch(
            id=str(uuid.uuid4()),
            repository_id=repository_id,
            name=name,
            head_commit_id=head_commit_id,
            created_from_commit_id=head_commit_id
        )
        self.db.add(branch)
        self.db.commit()
        self.db.refresh(branch)

        self.audit.record_event(
            "branch_create",
            entity_id=branch.id,
            payload={"name": name, "repository_id": repository_id, "from_commit_id": head_commit_id}
        )
        logger.info(f"Created branch '{name}' in repository '{repository_id}' from commit '{head_commit_id}'")
        return branch

    # Commit and Snapshot
    def create_commit(
        self,
        repository_id: str,
        commit_data: CommitCreate
    ) -> Commit:
        repo = self.get_repository(repository_id)
        if not repo:
            raise ValueError(f"Repository '{repository_id}' not found.")

        branch = self.get_branch(repository_id, commit_data.branch)
        if not branch:
            # Auto-create branch if it does not exist
            branch = self.create_branch(repository_id, commit_data.branch)

        parent_commit_ids = [branch.head_commit_id] if branch.head_commit_id else []

        commit_id = str(uuid.uuid4())
        raw_items_dict = []
        snapshot_records = []

        for item in commit_data.items:
            mem_id = str(uuid.uuid4())
            cat_val = item.category.value if hasattr(item.category, "value") else str(item.category)
            act_val = (
                item.retention_action.value
                if (item.retention_action and hasattr(item.retention_action, "value"))
                else (str(item.retention_action) if item.retention_action else "retain")
            )
            item_dict = {
                "memory_item_id": mem_id,
                "logical_key": item.logical_key,
                "content": item.content.strip(),
                "category": cat_val,
                "topic": item.topic,
                "source_message_ids": item.source_message_ids,
                "retention_action": act_val,
                "confidence": item.confidence,
                "rationale": item.rationale
            }
            raw_items_dict.append(item_dict)

            snap_rec = SnapshotItem(
                id=str(uuid.uuid4()),
                commit_id=commit_id,
                memory_item_id=mem_id,
                logical_key=item.logical_key,
                content_at_commit=item.content.strip(),
                category_at_commit=cat_val,
                topic_at_commit=item.topic,
                source_message_ids=item.source_message_ids,
                retention_action_at_commit=act_val,
                confidence_at_commit=item.confidence,
                rationale_at_commit=item.rationale
            )
            snapshot_records.append(snap_rec)

        snapshot_hash = compute_snapshot_hash(raw_items_dict)

        commit = Commit(
            id=commit_id,
            repository_id=repository_id,
            branch_id=branch.id,
            parent_commit_ids=parent_commit_ids,
            message=commit_data.message.strip(),
            snapshot_hash=snapshot_hash,
            author=commit_data.author or "user"
        )
        self.db.add(commit)
        for snap in snapshot_records:
            self.db.add(snap)

        # Update branch head
        branch.head_commit_id = commit_id

        self.db.commit()
        self.db.refresh(commit)

        self.audit.record_event(
            "commit",
            actor=commit.author,
            entity_id=commit.id,
            payload={
                "branch": branch.name,
                "message": commit.message,
                "snapshot_hash": snapshot_hash,
                "item_count": len(snapshot_records)
            }
        )
        logger.info(f"Created commit {commit.id} on branch '{branch.name}' (hash={snapshot_hash[:8]})")
        return commit

    def get_commit(self, commit_id: str) -> Optional[Commit]:
        stmt = select(Commit).where(Commit.id == commit_id)
        return self.db.scalars(stmt).first()

    def get_commit_items(self, commit_id: str) -> List[SnapshotItem]:
        stmt = (
            select(SnapshotItem)
            .where(SnapshotItem.commit_id == commit_id)
            .order_by(SnapshotItem.id.asc())
        )
        return list(self.db.scalars(stmt).all())

    def verify_commit_integrity(self, commit_id: str) -> bool:
        """Verify that the stored snapshot items match the commit snapshot_hash."""
        commit = self.get_commit(commit_id)
        if not commit:
            return False
        items = self.get_commit_items(commit_id)
        items_dict = [
            {
                "logical_key": i.logical_key,
                "content_at_commit": i.content_at_commit,
                "category_at_commit": i.category_at_commit,
                "topic_at_commit": i.topic_at_commit,
                "source_message_ids": i.source_message_ids,
                "retention_action_at_commit": i.retention_action_at_commit
            }
            for i in items
        ]
        calculated_hash = compute_snapshot_hash(items_dict)
        return calculated_hash == commit.snapshot_hash

    def list_branch_history(self, repository_id: str, branch_name: str) -> List[Commit]:
        branch = self.get_branch(repository_id, branch_name)
        if not branch:
            raise ValueError(f"Branch '{branch_name}' not found.")
        if not branch.head_commit_id:
            return []

        # Traverse commit history from head commit
        commits: List[Commit] = []
        visited = set()
        queue = [branch.head_commit_id]

        while queue:
            curr_id = queue.pop(0)
            if curr_id in visited:
                continue
            visited.add(curr_id)

            c = self.get_commit(curr_id)
            if c:
                commits.append(c)
                for pid in c.parent_commit_ids:
                    if pid not in visited:
                        queue.append(pid)

        # Sort commits chronologically descending
        commits.sort(key=lambda x: x.created_at, reverse=True)
        return commits

    # Restore
    def restore_snapshot(
        self,
        repository_id: str,
        branch_name: str,
        target_commit_id: str,
        message: Optional[str] = None
    ) -> Commit:
        """Restore a historical commit by creating a new commit on the branch."""
        target_commit = self.get_commit(target_commit_id)
        if not target_commit:
            raise ValueError(f"Historical commit '{target_commit_id}' not found.")

        # Verify target commit integrity first
        if not self.verify_commit_integrity(target_commit_id):
            raise ValueError(f"Snapshot integrity verification failed for commit '{target_commit_id}'.")

        historical_items = self.get_commit_items(target_commit_id)
        new_items_data = [
            MemoryItemCreate(
                logical_key=item.logical_key,
                content=item.content_at_commit,
                category=item.category_at_commit,  # type: ignore
                topic=item.topic_at_commit,
                source_message_ids=item.source_message_ids,
                rationale=f"Restored from historical snapshot {target_commit_id[:8]}",
                confidence=item.confidence_at_commit,
                retention_action=item.retention_action_at_commit  # type: ignore
            )
            for item in historical_items
        ]

        restore_msg = message or f"Restore snapshot from commit {target_commit_id[:8]}"
        commit_data = CommitCreate(
            branch=branch_name,
            message=restore_msg,
            items=new_items_data,
            author="user"
        )
        new_commit = self.create_commit(repository_id, commit_data)

        self.audit.record_event(
            "restore",
            entity_id=new_commit.id,
            payload={
                "branch": branch_name,
                "restored_from_commit": target_commit_id,
                "new_commit_id": new_commit.id
            }
        )
        logger.info(f"Restored commit {target_commit_id} to branch '{branch_name}' as new commit {new_commit.id}")
        return new_commit

    # Diff
    def diff_commits(self, base_commit_id: str, target_commit_id: str) -> CommitDiffResponse:
        base_items = self.get_commit_items(base_commit_id)
        target_items = self.get_commit_items(target_commit_id)

        base_map = {(i.logical_key or i.content_at_commit): i for i in base_items}
        target_map = {(i.logical_key or i.content_at_commit): i for i in target_items}

        added = []
        removed = []
        modified = []

        for key, item in target_map.items():
            if key not in base_map:
                added.append(SnapshotItemResponse.model_validate(item))
            elif base_map[key].content_at_commit != item.content_at_commit:
                modified.append({
                    "key": key,
                    "base": SnapshotItemResponse.model_validate(base_map[key]).model_dump(),
                    "target": SnapshotItemResponse.model_validate(item).model_dump()
                })

        for key, item in base_map.items():
            if key not in target_map:
                removed.append(SnapshotItemResponse.model_validate(item))

        return CommitDiffResponse(
            base_commit_id=base_commit_id,
            target_commit_id=target_commit_id,
            added_items=added,
            removed_items=removed,
            modified_items=modified
        )

    # Merge
    def check_merge_conflicts(
        self,
        repository_id: str,
        source_branch_name: str,
        target_branch_name: str,
        selected_memory_item_ids: List[str]
    ) -> Tuple[List[MergeConflictDetail], List[SnapshotItem], List[SnapshotItem]]:
        source_b = self.get_branch(repository_id, source_branch_name)
        target_b = self.get_branch(repository_id, target_branch_name)
        if not source_b or not source_b.head_commit_id:
            raise ValueError(f"Source branch '{source_branch_name}' has no commits.")
        if not target_b or not target_b.head_commit_id:
            raise ValueError(f"Target branch '{target_branch_name}' has no commits.")

        source_items = self.get_commit_items(source_b.head_commit_id)
        target_items = self.get_commit_items(target_b.head_commit_id)

        # Filter selected items from source
        selected_source_items = [
            i for i in source_items if (i.memory_item_id in selected_memory_item_ids or i.id in selected_memory_item_ids)
        ]
        if not selected_source_items:
            raise ValueError("None of the selected items were found in the source branch snapshot.")

        target_key_map = {
            i.logical_key: i for i in target_items if i.logical_key
        }

        conflicts: List[MergeConflictDetail] = []
        for s_item in selected_source_items:
            if s_item.logical_key and s_item.logical_key in target_key_map:
                t_item = target_key_map[s_item.logical_key]
                if s_item.content_at_commit.strip() != t_item.content_at_commit.strip():
                    conflicts.append(
                        MergeConflictDetail(
                            logical_key=s_item.logical_key,
                            source_item={
                                "id": s_item.memory_item_id,
                                "content": s_item.content_at_commit,
                                "topic": s_item.topic_at_commit,
                                "category": s_item.category_at_commit
                            },
                            target_item={
                                "id": t_item.memory_item_id,
                                "content": t_item.content_at_commit,
                                "topic": t_item.topic_at_commit,
                                "category": t_item.category_at_commit
                            },
                            conflict_reason=f"Logical key '{s_item.logical_key}' has divergent content between '{source_branch_name}' and '{target_branch_name}'."
                        )
                    )

        return conflicts, selected_source_items, target_items

    def merge_branches(
        self,
        repository_id: str,
        source_branch_name: str,
        target_branch_name: str,
        selected_memory_item_ids: List[str],
        message: Optional[str] = None
    ) -> Commit:
        conflicts, selected_source_items, target_items = self.check_merge_conflicts(
            repository_id, source_branch_name, target_branch_name, selected_memory_item_ids
        )

        if conflicts:
            raise ValueError(f"Merge conflict detected for {len(conflicts)} items. Explicit resolution required.")

        source_b = self.get_branch(repository_id, source_branch_name)
        target_b = self.get_branch(repository_id, target_branch_name)

        # Combined items: target items + selected source items (replacing if same key or adding)
        merged_items_dict: Dict[str, MemoryItemCreate] = {}

        for t in target_items:
            key = t.logical_key or t.id
            merged_items_dict[key] = MemoryItemCreate(
                logical_key=t.logical_key,
                content=t.content_at_commit,
                category=t.category_at_commit,  # type: ignore
                topic=t.topic_at_commit,
                source_message_ids=t.source_message_ids,
                rationale=t.rationale_at_commit or "Retained from target branch",
                confidence=t.confidence_at_commit,
                retention_action=t.retention_action_at_commit  # type: ignore
            )

        for s in selected_source_items:
            key = s.logical_key or s.id
            merged_items_dict[key] = MemoryItemCreate(
                logical_key=s.logical_key,
                content=s.content_at_commit,
                category=s.category_at_commit,  # type: ignore
                topic=s.topic_at_commit,
                source_message_ids=s.source_message_ids,
                rationale=f"Merged from branch '{source_branch_name}'",
                confidence=s.confidence_at_commit,
                retention_action=s.retention_action_at_commit  # type: ignore
            )

        # Create two-parent commit on target branch
        commit_id = str(uuid.uuid4())
        raw_items_dict = []
        snapshot_records = []

        for item_data in merged_items_dict.values():
            mem_id = str(uuid.uuid4())
            cat_val = item_data.category.value if hasattr(item_data.category, "value") else str(item_data.category)
            act_val = (
                item_data.retention_action.value
                if (item_data.retention_action and hasattr(item_data.retention_action, "value"))
                else (str(item_data.retention_action) if item_data.retention_action else "retain")
            )
            raw_items_dict.append({
                "memory_item_id": mem_id,
                "logical_key": item_data.logical_key,
                "content": item_data.content.strip(),
                "category": cat_val,
                "topic": item_data.topic,
                "source_message_ids": item_data.source_message_ids,
                "retention_action": act_val
            })
            snapshot_records.append(
                SnapshotItem(
                    id=str(uuid.uuid4()),
                    commit_id=commit_id,
                    memory_item_id=mem_id,
                    logical_key=item_data.logical_key,
                    content_at_commit=item_data.content.strip(),
                    category_at_commit=cat_val,
                    topic_at_commit=item_data.topic,
                    source_message_ids=item_data.source_message_ids,
                    retention_action_at_commit=act_val,
                    confidence_at_commit=item_data.confidence,
                    rationale_at_commit=item_data.rationale
                )
            )

        snapshot_hash = compute_snapshot_hash(raw_items_dict)
        merge_commit = Commit(
            id=commit_id,
            repository_id=repository_id,
            branch_id=target_b.id,
            parent_commit_ids=[target_b.head_commit_id, source_b.head_commit_id],
            message=message or f"Merge selected items from '{source_branch_name}' into '{target_branch_name}'",
            snapshot_hash=snapshot_hash,
            author="user"
        )
        self.db.add(merge_commit)
        for snap in snapshot_records:
            self.db.add(snap)

        target_b.head_commit_id = commit_id
        self.db.commit()
        self.db.refresh(merge_commit)

        self.audit.record_event(
            "merge",
            entity_id=merge_commit.id,
            payload={
                "source_branch": source_branch_name,
                "target_branch": target_branch_name,
                "parents": [target_b.head_commit_id, source_b.head_commit_id],
                "selected_items_count": len(selected_source_items)
            }
        )
        logger.info(f"Merged {len(selected_source_items)} items from '{source_branch_name}' to '{target_branch_name}' (commit {merge_commit.id})")
        return merge_commit

