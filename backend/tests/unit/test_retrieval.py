from sqlalchemy.orm import Session
from backend.app.services.version_service import VersionService
from backend.app.services.retrieval import RetrievalService
from backend.app.schemas.commit import CommitCreate
from backend.app.schemas.memory import MemoryItemCreate
from backend.app.schemas.common import MemoryCategory


def test_retrieval_ranking_and_provenance(db_session: Session):
    version_svc = VersionService(db_session)
    repo = version_svc.get_or_create_repository("retrieval-repo")

    # Create commit with multiple topics
    version_svc.create_commit(
        repo.id,
        CommitCreate(
            branch="main",
            message="Initial knowledge base",
            items=[
                MemoryItemCreate(
                    logical_key="project.database",
                    content="We selected PostgreSQL version 16 with pgvector extension.",
                    category=MemoryCategory.DECISION,
                    topic="database",
                    source_message_ids=["msg-42"],
                    rationale="Scalable storage decision"
                ),
                MemoryItemCreate(
                    logical_key="architecture.framework",
                    content="FastAPI is configured for the REST API server.",
                    category=MemoryCategory.DECISION,
                    topic="backend",
                    source_message_ids=["msg-10"],
                    rationale="Backend choice"
                ),
                MemoryItemCreate(
                    logical_key="system.security",
                    content="Always hash user passwords using Argon2id.",
                    category=MemoryCategory.CONSTRAINT,
                    topic="security",
                    source_message_ids=["msg-99"],
                    rationale="Security policy"
                )
            ]
        )
    )

    retrieval_svc = RetrievalService(db_session)
    resp = retrieval_svc.retrieve(repo.id, query="Which database did we select?", branch_name="main", top_k=2)

    assert len(resp.results) > 0
    top = resp.results[0]
    assert "postgresql" in top.content.lower()
    assert top.topic == "database"
    assert "msg-42" in top.source_message_ids
    assert top.commit_id is not None
    assert "source: msg-42" in resp.context_text

