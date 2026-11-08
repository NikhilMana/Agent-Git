import os
import tempfile
from sqlalchemy.orm import Session
from backend.app.services.version_service import VersionService
from backend.app.services.codebase_indexer import CodebaseIndexer
from backend.app.services.context_orchestrator import ContextOrchestrator
from backend.app.schemas.commit import CommitCreate
from backend.app.schemas.memory import MemoryItemCreate
from backend.app.schemas.task_context import TaskContextRequest
from backend.app.schemas.common import MemoryCategory


def test_context_orchestrator_ranking_and_budgeting(db_session: Session):
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create a sample file
        auth_file = os.path.join(tmp_dir, "auth_service.py")
        with open(auth_file, "w") as f:
            f.write(
                "class AuthTokenHandler:\n"
                "    def create_access_token(self): pass\n"
            )

        indexer = CodebaseIndexer(db_session, repository_root=tmp_dir)
        version_svc = VersionService(db_session)
        repo = version_svc.get_or_create_repository("orchestrator-repo")

        # Index the codebase
        indexer.index_repository(repo.id)

        # Create a historical commit with constraints and decisions
        version_svc.create_commit(
            repo.id,
            CommitCreate(
                branch="main",
                message="Security decisions",
                items=[
                    MemoryItemCreate(
                        logical_key="system.auth",
                        content="We must never store tokens in plaintext.",
                        category=MemoryCategory.CONSTRAINT,
                        topic="security",
                        source_message_ids=["msg-sec-01"],
                        rationale="Security constraint"
                    ),
                    MemoryItemCreate(
                        logical_key="system.jwt",
                        content="Decided to use RS256 for signing tokens.",
                        category=MemoryCategory.DECISION,
                        topic="security",
                        source_message_ids=["msg-sec-02"],
                        rationale="Decision on token algorithm"
                    )
                ]
            )
        )

        orchestrator = ContextOrchestrator(db_session, repository_root=tmp_dir)

        # 1. Full request
        req = TaskContextRequest(
            task="Implement create_access_token in auth_service",
            repository_id=repo.id,
            branch="main",
            current_file="auth_service.py",
            max_tokens=3500
        )
        res = orchestrator.get_task_context(req)

        assert res.repository_id == repo.id
        assert len(res.relevant_files) >= 1
        assert res.relevant_files[0].relative_path == "auth_service.py"
        assert res.coverage in ["high", "partial"]
        assert len(res.context_sections.get("constraints", [])) >= 1
        assert len(res.context_sections.get("decisions", [])) >= 1
        assert "file:auth_service.py" in res.sources
        assert "msg-sec-01" in res.sources or "msg-sec-02" in res.sources

        # 2. Strict token budget test
        tight_req = TaskContextRequest(
            task="Implement create_access_token in auth_service",
            repository_id=repo.id,
            branch="main",
            current_file="auth_service.py",
            max_tokens=40  # very low budget
        )
        tight_res = orchestrator.get_task_context(tight_req)
        assert len(tight_res.omitted_items) > 0 or tight_res.estimated_tokens <= 100

