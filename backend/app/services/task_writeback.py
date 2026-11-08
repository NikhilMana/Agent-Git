import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.app.schemas.task_context import TaskOutcomeRequest
from backend.app.schemas.commit import CommitCreate
from backend.app.schemas.memory import MemoryItemCreate
from backend.app.schemas.common import MemoryCategory, RetentionAction
from backend.app.services.version_service import VersionService
from backend.app.core.logging import logger


class TaskWritebackService:
    def __init__(self, db: Session):
        self.db = db
        self.version_service = VersionService(db)

    def record_task_outcome(self, outcome_data: TaskOutcomeRequest) -> Dict[str, Any]:
        repo_id = outcome_data.repository_id
        branch_name = outcome_data.branch or "main"

        # Ensure repository exists
        repo = self.version_service.get_or_create_repository(repo_id)

        items_to_commit: List[MemoryItemCreate] = []

        # 1. Decisions
        for idx, dec in enumerate(outcome_data.decisions or []):
            if not dec.strip():
                continue
            items_to_commit.append(
                MemoryItemCreate(
                    logical_key=f"task.decision.{idx+1}",
                    content=dec.strip(),
                    category=MemoryCategory.DECISION,
                    topic="task-outcome",
                    source_message_ids=[outcome_data.commit_hash or f"task-{uuid.uuid4().hex[:6]}"],
                    rationale=f"Verified decision made during task '{outcome_data.task}'",
                    confidence=0.98,
                    retention_action=RetentionAction.RETAIN
                )
            )

        # 2. Outcome Summary
        if outcome_data.outcome_summary.strip():
            items_to_commit.append(
                MemoryItemCreate(
                    logical_key="task.summary",
                    content=f"Task: {outcome_data.task}. Outcome: {outcome_data.outcome_summary.strip()}",
                    category=MemoryCategory.SUMMARY,
                    topic="task-outcome",
                    source_message_ids=[outcome_data.commit_hash or f"task-{uuid.uuid4().hex[:6]}"],
                    rationale="High-level verified task outcome summary.",
                    confidence=0.95,
                    retention_action=RetentionAction.SUMMARIZE
                )
            )

        # 3. Unresolved issues / follow-up tasks
        for idx, issue in enumerate(outcome_data.unresolved_issues or []):
            if not issue.strip():
                continue
            items_to_commit.append(
                MemoryItemCreate(
                    logical_key=f"task.unresolved.{idx+1}",
                    content=issue.strip(),
                    category=MemoryCategory.TASK,
                    topic="task-outcome",
                    source_message_ids=[outcome_data.commit_hash or f"task-{uuid.uuid4().hex[:6]}"],
                    rationale=f"Unresolved issue flagged during task '{outcome_data.task}'",
                    confidence=0.92,
                    retention_action=RetentionAction.RETAIN
                )
            )

        # 4. Verified Changes & Tests
        files_str = ", ".join(outcome_data.changed_files or []) or "none"
        tests_str = ", ".join(outcome_data.tests_run or []) or "none"
        verif_content = (
            f"Task '{outcome_data.task}' modified files: [{files_str}]. "
            f"Tests run: [{tests_str}], status: {outcome_data.test_results}."
        )
        items_to_commit.append(
            MemoryItemCreate(
                logical_key="task.verification",
                content=verif_content,
                category=MemoryCategory.FACT,
                topic="task-outcome",
                source_message_ids=[outcome_data.commit_hash or f"task-{uuid.uuid4().hex[:6]}"],
                rationale="Verified code modification and test validation record.",
                confidence=0.99,
                retention_action=RetentionAction.RETAIN
            )
        )

        commit_msg = f"Task write-back: {outcome_data.task[:80]}"
        commit_create = CommitCreate(
            branch=branch_name,
            message=commit_msg,
            items=items_to_commit,
            author="agent"
        )

        commit = self.version_service.create_commit(repo.id, commit_create)

        logger.info(
            f"Task outcome recorded for task '{outcome_data.task}' on branch '{branch_name}'. "
            f"Created commit {commit.id} with {len(items_to_commit)} memory items."
        )

        return {
            "status": "recorded",
            "repository_id": repo.id,
            "branch": branch_name,
            "commit_id": commit.id,
            "snapshot_hash": commit.snapshot_hash,
            "items_committed_count": len(items_to_commit),
            "decisions_recorded": len(outcome_data.decisions or []),
            "unresolved_recorded": len(outcome_data.unresolved_issues or [])
        }

