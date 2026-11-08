import json
from sqlalchemy.orm import Session
from backend.app.mcp.server import (
    set_db_override,
    agentgit_get_task_context,
    agentgit_search_memory,
    agentgit_commit_memory,
    agentgit_get_memory_history,
    agentgit_create_branch,
    agentgit_merge_branch,
    agentgit_restore_snapshot,
    agentgit_record_task_outcome,
    agentgit_refresh_codebase_index,
    agentgit_get_file_context
)
from backend.app.services.version_service import VersionService


def test_mcp_tools_execution(db_session: Session):
    set_db_override(db_session)
    try:
        version_svc = VersionService(db_session)
        repo = version_svc.get_or_create_repository("mcp-test-repo")

        # 1. Commit memory via MCP tool
        commit_res = json.loads(
            agentgit_commit_memory(
                branch="main",
                message="Initial MCP commit",
                items=[
                    {
                        "logical_key": "project.database",
                        "content": "Database is PostgreSQL.",
                        "category": "decision",
                        "topic": "database",
                        "source_message_ids": ["mcp-msg-1"]
                    }
                ],
                repository_id=repo.id
            )
        )
        assert commit_res["status"] == "committed"
        assert "commit_id" in commit_res
        c1_id = commit_res["commit_id"]

        # 2. Get history via MCP tool
        hist_res = json.loads(agentgit_get_memory_history(repository_id=repo.id, branch="main"))
        assert hist_res["commit_count"] >= 1
        assert hist_res["commits"][0]["commit_id"] == c1_id

        # 3. Create branch via MCP tool
        branch_res = json.loads(agentgit_create_branch("exp-branch", repository_id=repo.id, from_commit_id=c1_id))
        assert branch_res["status"] == "created"
        assert branch_res["name"] == "exp-branch"

        # 4. Search memory via MCP tool
        search_res = json.loads(agentgit_search_memory("Which database?", repository_id=repo.id, branch="main"))
        assert len(search_res["results"]) > 0
        assert "postgresql" in search_res["results"][0]["content"].lower()

        # 5. Record task outcome via MCP tool
        outcome_res = json.loads(
            agentgit_record_task_outcome(
                repository_id=repo.id,
                branch="main",
                task="Add security headers",
                outcome_summary="Added CSP and HSTS headers.",
                decisions=["Enforce HTTPS across all endpoints."],
                changed_files=["app/main.py"],
                tests_run=["tests/test_health.py"],
                test_results="passed"
            )
        )
        assert outcome_res["status"] == "recorded"
        assert outcome_res["decisions_recorded"] == 1

        # 6. Get task context via MCP tool
        ctx_res = json.loads(
            agentgit_get_task_context(
                task="Verify security headers",
                repository_id=repo.id,
                branch="main"
            )
        )
        assert ctx_res["repository_id"] == repo.id
        assert "context_sections" in ctx_res

        # 7. Refresh codebase index via MCP tool
        refresh_res = json.loads(agentgit_refresh_codebase_index(repository_id=repo.id))
        assert "indexed_count" in refresh_res

        # 8. Restore snapshot via MCP tool
        restore_res = json.loads(
            agentgit_restore_snapshot(
                repository_id=repo.id,
                branch="main",
                commit_id=c1_id,
                message="Rollback to c1"
            )
        )
        assert restore_res["status"] == "restored"
        assert restore_res["restored_from"] == c1_id
    finally:
        set_db_override(None)
