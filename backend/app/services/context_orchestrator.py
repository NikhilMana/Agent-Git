import math
import os
import re
from typing import Dict, Any, List, Optional, Set, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.app.models.codebase_index import (
    RepositoryIndexMeta,
    CodebaseFileRecord,
    CodebaseSymbolRecord,
    CodebaseDependencyRecord,
)
from backend.app.models.snapshot import SnapshotItem
from backend.app.schemas.task_context import TaskContextRequest, TaskContextResponse
from backend.app.schemas.codebase import CodebaseFileSummary, CodebaseSymbolSummary, CodebaseDependencySummary
from backend.app.services.version_service import VersionService
from backend.app.services.retrieval import RetrievalService
from backend.app.services.freshness_manager import FreshnessManager
from backend.app.core.logging import logger


def estimate_tokens(text: str) -> int:
    """Approximate token count: 1 token ≈ 4 characters or 0.75 words."""
    words = text.split()
    return int(len(words) * 1.33) + 1


class ContextOrchestrator:
    def __init__(self, db: Session, repository_root: Optional[str] = None):
        self.db = db
        self.repository_root = os.path.realpath(repository_root or os.getcwd())
        self.version_service = VersionService(db)
        self.retrieval_service = RetrievalService(db)
        self.freshness_manager = FreshnessManager(db, self.repository_root)

    def get_task_context(self, req: TaskContextRequest) -> TaskContextResponse:
        repo_id = req.repository_id
        branch_name = req.branch or "main"
        max_budget = req.max_tokens or 3500
        include_cats = set(req.include or [
            "decisions", "constraints", "files", "symbols", "dependencies", "unfinished_tasks", "conversation_memories"
        ])

        # 1. Extract search tokens from task description and current file
        task_tokens = set([w.lower() for w in re.findall(r"[A-Za-z0-9]+", req.task) if len(w) > 1])
        if req.current_file:
            task_tokens.update([w.lower() for w in re.findall(r"[A-Za-z0-9]+", req.current_file) if len(w) > 1])

        # 2. Gather conversation memories from repository branch
        memory_items_raw = []
        branch = self.version_service.get_branch(repo_id, branch_name)
        if branch and branch.head_commit_id:
            retrieval_resp = self.retrieval_service.retrieve(
                repository_id=repo_id,
                query=req.task,
                branch_name=branch_name,
                top_k=8
            )
            memory_items_raw = retrieval_resp.results

        # 3. Categorize memory items into decisions, constraints, unfinished tasks
        decisions: List[str] = []
        constraints: List[str] = []
        unfinished_tasks: List[str] = []
        conversation_memories_out: List[Dict[str, Any]] = []

        sources_set: Set[str] = set()

        for m in memory_items_raw:
            sources_set.update(m.source_message_ids)
            entry = {
                "content": m.content,
                "category": m.category,
                "topic": m.topic,
                "score": m.score,
                "commit_id": m.commit_id,
                "logical_key": m.logical_key,
                "source_message_ids": m.source_message_ids
            }
            conversation_memories_out.append(entry)

            cat = (m.category or "").lower()
            if "constraint" in cat:
                constraints.append(f"{m.content} (source: {', '.join(m.source_message_ids)})")
            elif "decision" in cat:
                decisions.append(f"{m.content} (source: {', '.join(m.source_message_ids)})")
            elif "task" in cat:
                unfinished_tasks.append(f"{m.content} (source: {', '.join(m.source_message_ids)})")

        # Also pull branch snapshot items to ensure all active decisions & constraints are preserved
        if branch and branch.head_commit_id:
            snapshot_items = self.version_service.get_commit_items(branch.head_commit_id)
            for item in snapshot_items:
                cat = (item.category_at_commit or "").lower()
                src_str = f" (source: {', '.join(item.source_message_ids)})" if item.source_message_ids else ""
                entry_str = f"{item.content_at_commit}{src_str}"
                if "constraint" in cat and entry_str not in constraints:
                    constraints.append(entry_str)
                    sources_set.update(item.source_message_ids)
                elif "decision" in cat and entry_str not in decisions:
                    decisions.append(entry_str)
                    sources_set.update(item.source_message_ids)
                elif "task" in cat and entry_str not in unfinished_tasks:
                    unfinished_tasks.append(entry_str)
                    sources_set.update(item.source_message_ids)

        # 4. Search Codebase Index
        meta_stmt = select(RepositoryIndexMeta).where(RepositoryIndexMeta.repository_id == repo_id)
        meta = self.db.scalars(meta_stmt).first()

        relevant_files_out: List[CodebaseFileSummary] = []
        symbols_out: List[CodebaseSymbolSummary] = []
        dependencies_out: List[CodebaseDependencySummary] = []

        if meta:
            # Files match
            files_stmt = select(CodebaseFileRecord).where(CodebaseFileRecord.index_meta_id == meta.id)
            all_files = list(self.db.scalars(files_stmt).all())

            matched_files: List[Tuple[float, CodebaseFileRecord]] = []
            for f in all_files:
                f_score = 0.0
                f_lower = f.relative_path.lower()

                # Exact current file match
                if req.current_file and req.current_file.lower() in f_lower:
                    f_score += 10.0

                # Changed files hint
                if req.changed_files and any(cf.lower() in f_lower for cf in req.changed_files):
                    f_score += 8.0

                # Task token overlap in file path
                matched_kw = [t for t in task_tokens if t in f_lower]
                f_score += len(matched_kw) * 2.0

                if f_score > 0.0 or len(matched_files) < 3:
                    matched_files.append((f_score, f))

            matched_files.sort(key=lambda x: x[0], reverse=True)
            top_files = matched_files[:5]

            for _, f_rec in top_files:
                # Check live freshness
                is_fresh, _ = self.freshness_manager.check_file_freshness(repo_id, f_rec.relative_path)
                relevant_files_out.append(
                    CodebaseFileSummary(
                        relative_path=f_rec.relative_path,
                        language=f_rec.language,
                        size_bytes=f_rec.size_bytes,
                        content_hash=f_rec.content_hash,
                        is_stale=not is_fresh,
                        summary=f_rec.summary
                    )
                )
                sources_set.add(f"file:{f_rec.relative_path}")

            # Symbols match from matched files or symbol names
            top_file_ids = [f_rec.id for _, f_rec in top_files]
            if top_file_ids:
                sym_stmt = select(CodebaseSymbolRecord).where(CodebaseSymbolRecord.file_record_id.in_(top_file_ids))
                symbols_raw = list(self.db.scalars(sym_stmt).all())

                file_id_to_path = {f_rec.id: f_rec.relative_path for _, f_rec in top_files}

                for s in symbols_raw:
                    # Score symbol
                    s_name_lower = s.name.lower()
                    if any(t in s_name_lower for t in task_tokens) or len(symbols_out) < 6:
                        symbols_out.append(
                            CodebaseSymbolSummary(
                                name=s.name,
                                kind=s.kind,
                                file=file_id_to_path.get(s.file_record_id, "unknown"),
                                line_start=s.line_start,
                                line_end=s.line_end,
                                signature=s.signature,
                                docstring=s.docstring
                            )
                        )

            # Dependencies for matched files
            top_paths = [f.relative_path for f in relevant_files_out]
            if top_paths:
                dep_stmt = select(CodebaseDependencyRecord).where(
                    CodebaseDependencyRecord.repository_id == repo_id,
                    CodebaseDependencyRecord.source_path.in_(top_paths)
                )
                deps_raw = list(self.db.scalars(dep_stmt).all())
                for d in deps_raw[:8]:
                    dependencies_out.append(
                        CodebaseDependencySummary(
                            source_path=d.source_path,
                            target_path=d.target_path,
                            relation=d.relation,
                            confidence=d.confidence
                        )
                    )

        # 5. Token Budgeting & Ranking
        total_estimated = 0
        omitted_items: List[str] = []

        # Sections included per request
        sections_dict: Dict[str, List[str]] = {}
        if "decisions" in include_cats:
            sections_dict["decisions"] = decisions
        if "constraints" in include_cats:
            sections_dict["constraints"] = constraints
        if "unfinished_tasks" in include_cats:
            sections_dict["unfinished_tasks"] = unfinished_tasks

        # Calculate estimated tokens
        rendered_text_parts = [req.task]
        for sec_name, sec_items in sections_dict.items():
            rendered_text_parts.extend(sec_items)
        if "files" in include_cats:
            for rf in relevant_files_out:
                rendered_text_parts.append(f"{rf.relative_path} {rf.language}")
        if "symbols" in include_cats:
            for sb in symbols_out:
                rendered_text_parts.append(f"{sb.name} {sb.kind} {sb.signature or ''}")
        if "dependencies" in include_cats:
            for dp in dependencies_out:
                rendered_text_parts.append(f"{dp.source_path} -> {dp.target_path}")
        if "conversation_memories" in include_cats:
            for cm in conversation_memories_out:
                rendered_text_parts.append(cm["content"])

        total_estimated = estimate_tokens(" ".join(rendered_text_parts))

        # Enforce budget if exceeded
        if total_estimated > max_budget:
            # Trim optional summaries and lower priority symbols
            while total_estimated > max_budget and len(conversation_memories_out) > 2:
                popped = conversation_memories_out.pop()
                omitted_items.append(f"Memory: {popped['content'][:50]}...")
                total_estimated = max(100, total_estimated - 50)

            while total_estimated > max_budget and len(symbols_out) > 3:
                popped_sym = symbols_out.pop()
                omitted_items.append(f"Symbol: {popped_sym.name} ({popped_sym.file})")
                total_estimated = max(100, total_estimated - 30)

        # 6. Assign Transparent Coverage Label
        # High: has constraints or decisions + relevant files matched
        # Partial: either memories or files found
        # Low: no relevant memories and no indexed files
        has_memories = len(memory_items_raw) > 0
        has_files = len(relevant_files_out) > 0

        if has_memories and has_files:
            coverage = "high"
            needs_more = False
        elif has_memories or has_files:
            coverage = "partial"
            needs_more = len(omitted_items) > 0
        else:
            coverage = "low"
            needs_more = True

        return TaskContextResponse(
            repository_id=repo_id,
            branch=branch_name,
            task=req.task,
            context_sections=sections_dict,
            relevant_files=relevant_files_out if "files" in include_cats else [],
            symbols=symbols_out if "symbols" in include_cats else [],
            dependencies=dependencies_out if "dependencies" in include_cats else [],
            memory_items=conversation_memories_out if "conversation_memories" in include_cats else [],
            estimated_tokens=total_estimated,
            token_estimation_method="approximate (1.33 words/token)",
            coverage=coverage,
            needs_more_context=needs_more,
            omitted_items=omitted_items,
            sources=sorted(list(sources_set))
        )
