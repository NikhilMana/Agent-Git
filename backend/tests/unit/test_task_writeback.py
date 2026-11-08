from sqlalchemy.orm import Session
from backend.app.services.task_writeback import TaskWritebackService
from backend.app.schemas.task_context import TaskOutcomeRequest
from backend.app.services.version_service import VersionService


def test_task_writeback_creates_commit_and_items(db_session: Session):
    version_svc = VersionService(db_session)
    repo = version_svc.get_or_create_repository("writeback-repo")
    writeback_svc = TaskWritebackService(db_session)

    req = TaskOutcomeRequest(
        repository_id=repo.id,
        branch="main",
        task="Implement JWT token authentication",
        outcome_summary="Added JWT token generation and verification middleware.",
        decisions=[
            "Use RS256 algorithm with 2048-bit RSA keys.",
            "Set access token lifetime to 15 minutes."
        ],
        changed_files=["app/auth.py", "app/main.py"],
        symbols_changed=["generate_token", "verify_token"],
        tests_run=["tests/test_auth.py"],
        test_results="passed",
        unresolved_issues=["Add refresh token rotation in next milestone"],
        commit_hash="abc1234"
    )

    result = writeback_svc.record_task_outcome(req)
    assert result["status"] == "recorded"
    assert result["commit_id"] is not None
    assert result["decisions_recorded"] == 2
    assert result["unresolved_recorded"] == 1
    assert result["items_committed_count"] >= 4

    # Verify commit exists on branch
    history = version_svc.list_branch_history(repo.id, "main")
    assert len(history) == 1
    commit = history[0]
    assert commit.id == result["commit_id"]
    assert "Task write-back" in commit.message

    # Verify commit items
    items = version_svc.get_commit_items(commit.id)
    assert len(items) == result["items_committed_count"]
    categories = {i.category_at_commit for i in items}
    assert "decision" in categories
    assert "summary" in categories
    assert "task" in categories
    assert "fact" in categories

