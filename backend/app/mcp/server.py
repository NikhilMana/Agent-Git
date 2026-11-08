import json
import os
import sys
from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP

from backend.app.db.session import SessionLocal, create_all_tables
from backend.app.services.version_service import VersionService
from backend.app.services.retrieval import RetrievalService
from backend.app.services.codebase_indexer import CodebaseIndexer
from backend.app.services.freshness_manager import FreshnessManager
from backend.app.services.task_writeback import TaskWritebackService
from backend.app.services.context_orchestrator import ContextOrchestrator
from backend.app.schemas.task_context import TaskContextRequest, TaskOutcomeRequest
from backend.app.schemas.commit import CommitCreate
from backend.app.schemas.memory import MemoryItemCreate
from backend.app.core.logging import logger

mcp = FastMCP("agentgit")

_db_override = None


def set_db_override(session):
    """Override session for testing."""
    global _db_override
    _db_override = session


def _get_db():
    if _db_override is not None:
        return _db_override
    create_all_tables()
    return SessionLocal()


def _close_db(db):
    if _db_override is None and db is not None:
        db.close()


# ---------------------------------------------------------------------------
# Tool 1: agentgit_get_task_context
# ---------------------------------------------------------------------------
@mcp.tool()
def agentgit_get_task_context(
    task: str,
    repository_id: str = "default",
    branch: str = "main",
    current_file: Optional[str] = None,
    max_tokens: int = 3500,
    include: Optional[List[str]] = None,
    changed_files: Optional[List[str]] = None
) -> str:
    """Retrieve task-specific conversation memory, codebase metadata, symbols, and dependencies."""
    db = _get_db()
    try:
        version_svc = VersionService(db)
        repo = version_svc.get_or_create_repository(repository_id)
        orchestrator = ContextOrchestrator(db)
        req = TaskContextRequest(
            task=task,
            repository_id=repo.id,
            branch=branch,
            current_file=current_file,
            max_tokens=max_tokens,
            include=include or [
                "decisions", "constraints", "files", "symbols", "dependencies", "unfinished_tasks", "conversation_memories"
            ],
            changed_files=changed_files
        )
        response = orchestrator.get_task_context(req)
        return json.dumps(response.model_dump(), indent=2)
    except Exception as e:
        logger.error(f"Error in agentgit_get_task_context: {e}")
        return json.dumps({"error": {"code": "CONTEXT_RETRIEVAL_FAILED", "message": str(e)}})
    finally:
        _close_db(db)


# ---------------------------------------------------------------------------
# Tool 2: agentgit_search_memory
# ---------------------------------------------------------------------------
@mcp.tool()
def agentgit_search_memory(
    query: str,
    repository_id: str = "default",
    branch: str = "main",
    top_k: int = 5
) -> str:
    """Search conversation and project memories with relevance scores and source provenance."""
    db = _get_db()
    try:
        version_svc = VersionService(db)
        repo = version_svc.get_or_create_repository(repository_id)
        retrieval_svc = RetrievalService(db)
        resp = retrieval_svc.retrieve(
            repository_id=repo.id,
            query=query,
            branch_name=branch,
            top_k=top_k
        )
        return json.dumps(resp.model_dump(), indent=2)
    except Exception as e:
        return json.dumps({"error": {"code": "SEARCH_MEMORY_FAILED", "message": str(e)}})
    finally:
        _close_db(db)


# ---------------------------------------------------------------------------
# Tool 3: agentgit_get_file_context
# ---------------------------------------------------------------------------
@mcp.tool()
def agentgit_get_file_context(
    relative_path: str,
    repository_id: str = "default",
    max_tokens: int = 1500
) -> str:
    """Get indexed symbols, dependencies, and metadata for a specific repository file."""
    db = _get_db()
    try:
        freshness = FreshnessManager(db)
        is_fresh, freshness_reason = freshness.check_file_freshness(repository_id, relative_path)

        from backend.app.models.codebase_index import CodebaseFileRecord, CodebaseSymbolRecord, CodebaseDependencyRecord, RepositoryIndexMeta
        from sqlalchemy import select

        stmt = (
            select(CodebaseFileRecord)
            .join(RepositoryIndexMeta)
            .where(
                RepositoryIndexMeta.repository_id == repository_id,
                CodebaseFileRecord.relative_path == relative_path
            )
        )
        file_rec = db.scalars(stmt).first()
        if not file_rec:
            return json.dumps({
                "relative_path": relative_path,
                "is_indexed": False,
                "freshness": "unknown",
                "message": "File is not indexed. Inspect live file directly."
            })

        sym_stmt = select(CodebaseSymbolRecord).where(CodebaseSymbolRecord.file_record_id == file_rec.id)
        symbols = [
            {"name": s.name, "kind": s.kind, "lines": f"{s.line_start}-{s.line_end}", "signature": s.signature}
            for s in db.scalars(sym_stmt).all()
        ]

        dep_stmt = select(CodebaseDependencyRecord).where(
            CodebaseDependencyRecord.repository_id == repository_id,
            CodebaseDependencyRecord.source_path == relative_path
        )
        deps = [
            {"target": d.target_path, "relation": d.relation}
            for d in db.scalars(dep_stmt).all()
        ]

        return json.dumps({
            "relative_path": relative_path,
            "language": file_rec.language,
            "size_bytes": file_rec.size_bytes,
            "content_hash": file_rec.content_hash,
            "is_fresh": is_fresh,
            "freshness_reason": freshness_reason,
            "symbols": symbols,
            "dependencies": deps,
            "notice": "Live file on disk remains authoritative. Verify content before editing."
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": {"code": "FILE_CONTEXT_FAILED", "message": str(e)}})
    finally:
        _close_db(db)


# ---------------------------------------------------------------------------
# Tool 4: agentgit_record_task_outcome
# ---------------------------------------------------------------------------
@mcp.tool()
def agentgit_record_task_outcome(
    task: str,
    outcome_summary: str,
    repository_id: str = "default",
    branch: str = "main",
    decisions: Optional[List[str]] = None,
    changed_files: Optional[List[str]] = None,
    symbols_changed: Optional[List[str]] = None,
    tests_run: Optional[List[str]] = None,
    test_results: str = "passed",
    unresolved_issues: Optional[List[str]] = None,
    commit_hash: Optional[str] = None
) -> str:
    """Record verified task outcome, decisions, changed files, and test validation into an immutable memory commit."""
    db = _get_db()
    try:
        writeback = TaskWritebackService(db)
        req = TaskOutcomeRequest(
            repository_id=repository_id,
            branch=branch,
            task=task,
            outcome_summary=outcome_summary,
            decisions=decisions or [],
            changed_files=changed_files or [],
            symbols_changed=symbols_changed or [],
            tests_run=tests_run or [],
            test_results=test_results,
            unresolved_issues=unresolved_issues or [],
            commit_hash=commit_hash
        )
        res = writeback.record_task_outcome(req)
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"error": {"code": "TASK_WRITEBACK_FAILED", "message": str(e)}})
    finally:
        _close_db(db)


# ---------------------------------------------------------------------------
# Tool 5: agentgit_refresh_codebase_index
# ---------------------------------------------------------------------------
@mcp.tool()
def agentgit_refresh_codebase_index(
    repository_id: str = "default",
    git_commit: Optional[str] = None
) -> str:
    """Incrementally refresh the codebase metadata index for the repository."""
    db = _get_db()
    try:
        indexer = CodebaseIndexer(db)
        report = indexer.index_repository(repository_id, git_commit=git_commit)
        return json.dumps(report.model_dump(), indent=2)
    except Exception as e:
        return json.dumps({"error": {"code": "INDEX_REFRESH_FAILED", "message": str(e)}})
    finally:
        _close_db(db)


# ---------------------------------------------------------------------------
# Tool 6: agentgit_get_memory_history
# ---------------------------------------------------------------------------
@mcp.tool()
def agentgit_get_memory_history(
    repository_id: str = "default",
    branch: str = "main"
) -> str:
    """Get the commit history and snapshot hashes of a memory branch."""
    db = _get_db()
    try:
        version_svc = VersionService(db)
        repo = version_svc.get_or_create_repository(repository_id)
        commits = version_svc.list_branch_history(repo.id, branch)
        history = [
            {
                "commit_id": c.id,
                "message": c.message,
                "snapshot_hash": c.snapshot_hash,
                "parents": c.parent_commit_ids,
                "created_at": c.created_at.isoformat(),
                "author": c.author
            }
            for c in commits
        ]
        return json.dumps({"branch": branch, "commit_count": len(history), "commits": history}, indent=2)
    except Exception as e:
        return json.dumps({"error": {"code": "HISTORY_FAILED", "message": str(e)}})
    finally:
        _close_db(db)


# ---------------------------------------------------------------------------
# Tool 7: agentgit_commit_memory
# ---------------------------------------------------------------------------
@mcp.tool()
def agentgit_commit_memory(
    branch: str,
    message: str,
    items: List[Dict[str, Any]],
    repository_id: str = "default"
) -> str:
    """Create an immutable commit with reviewed memory items."""
    db = _get_db()
    try:
        version_svc = VersionService(db)
        repo = version_svc.get_or_create_repository(repository_id)
        items_objs = [
            MemoryItemCreate(
                logical_key=i.get("logical_key"),
                content=i.get("content", ""),
                category=i.get("category", "fact"),
                topic=i.get("topic", "general"),
                source_message_ids=i.get("source_message_ids", []),
                rationale=i.get("rationale", "Committed via MCP"),
                confidence=i.get("confidence", 1.0),
                retention_action=i.get("retention_action", "retain")
            )
            for i in items
        ]
        commit = version_svc.create_commit(
            repo.id,
            CommitCreate(branch=branch, message=message, items=items_objs)
        )
        return json.dumps({
            "status": "committed",
            "commit_id": commit.id,
            "branch": branch,
            "snapshot_hash": commit.snapshot_hash,
            "parent_commit_ids": commit.parent_commit_ids
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": {"code": "COMMIT_FAILED", "message": str(e)}})
    finally:
        _close_db(db)


# ---------------------------------------------------------------------------
# Tool 8: agentgit_create_branch
# ---------------------------------------------------------------------------
@mcp.tool()
def agentgit_create_branch(
    branch_name: str,
    repository_id: str = "default",
    from_commit_id: Optional[str] = None
) -> str:
    """Create a new independent memory branch from an existing commit or HEAD."""
    db = _get_db()
    try:
        version_svc = VersionService(db)
        repo = version_svc.get_or_create_repository(repository_id)
        branch = version_svc.create_branch(repo.id, branch_name, from_commit_id=from_commit_id)
        return json.dumps({
            "status": "created",
            "branch_id": branch.id,
            "name": branch.name,
            "head_commit_id": branch.head_commit_id
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": {"code": "BRANCH_FAILED", "message": str(e)}})
    finally:
        _close_db(db)


# ---------------------------------------------------------------------------
# Tool 9: agentgit_merge_branch
# ---------------------------------------------------------------------------
@mcp.tool()
def agentgit_merge_branch(
    source_branch: str,
    target_branch: str,
    selected_memory_item_ids: List[str],
    repository_id: str = "default",
    message: Optional[str] = None
) -> str:
    """Explicitly merge selected memory items into the target branch. Flags conflicts across matching logical keys."""
    db = _get_db()
    try:
        version_svc = VersionService(db)
        repo = version_svc.get_or_create_repository(repository_id)

        # Check conflicts first
        conflicts, _, _ = version_svc.check_merge_conflicts(
            repo.id, source_branch, target_branch, selected_memory_item_ids
        )
        if conflicts:
            return json.dumps({
                "error": {
                    "code": "MERGE_CONFLICT",
                    "message": f"Conflict detected across {len(conflicts)} logical keys. Explicit resolution required."
                },
                "conflicts": [c.model_dump() for c in conflicts]
            }, indent=2)

        commit = version_svc.merge_branches(
            repo.id,
            source_branch_name=source_branch,
            target_branch_name=target_branch,
            selected_memory_item_ids=selected_memory_item_ids,
            message=message
        )
        return json.dumps({
            "status": "merged",
            "commit_id": commit.id,
            "parents": commit.parent_commit_ids,
            "snapshot_hash": commit.snapshot_hash
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": {"code": "MERGE_FAILED", "message": str(e)}})
    finally:
        _close_db(db)


# ---------------------------------------------------------------------------
# Tool 10: agentgit_restore_snapshot
# ---------------------------------------------------------------------------
@mcp.tool()
def agentgit_restore_snapshot(
    commit_id: str,
    branch: str = "main",
    repository_id: str = "default",
    message: Optional[str] = None
) -> str:
    """Restore historical memory state by creating a new forward commit (non-destructive)."""
    db = _get_db()
    try:
        version_svc = VersionService(db)
        repo = version_svc.get_or_create_repository(repository_id)
        new_commit = version_svc.restore_snapshot(
            repo.id,
            branch_name=branch,
            target_commit_id=commit_id,
            message=message
        )
        return json.dumps({
            "status": "restored",
            "new_commit_id": new_commit.id,
            "restored_from": commit_id,
            "snapshot_hash": new_commit.snapshot_hash
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": {"code": "RESTORE_FAILED", "message": str(e)}})
    finally:
        _close_db(db)


# ---------------------------------------------------------------------------
# MCP Resources
# ---------------------------------------------------------------------------
@mcp.resource("agentgit://repositories/{repository_id}/overview")
def get_repository_overview(repository_id: str) -> str:
    """Read-only overview of a repository's branches and commit counts."""
    db = _get_db()
    try:
        version_svc = VersionService(db)
        repo = version_svc.get_or_create_repository(repository_id)
        branches = version_svc.list_branches(repo.id)
        return json.dumps({
            "repository_id": repo.id,
            "name": repo.name,
            "default_branch": repo.default_branch,
            "branches": [{"name": b.name, "head": b.head_commit_id} for b in branches]
        }, indent=2)
    finally:
        _close_db(db)


@mcp.resource("agentgit://repositories/{repository_id}/branches/{branch}/memory")
def get_branch_memory_resource(repository_id: str, branch: str) -> str:
    """Read-only view of active snapshot memory items on a branch."""
    db = _get_db()
    try:
        version_svc = VersionService(db)
        repo = version_svc.get_or_create_repository(repository_id)
        b = version_svc.get_branch(repo.id, branch)
        if not b or not b.head_commit_id:
            return json.dumps({"branch": branch, "items": []})
        items = version_svc.get_commit_items(b.head_commit_id)
        return json.dumps({
            "branch": branch,
            "head_commit_id": b.head_commit_id,
            "items": [
                {"key": i.logical_key, "content": i.content_at_commit, "topic": i.topic_at_commit}
                for i in items
            ]
        }, indent=2)
    finally:
        _close_db(db)


@mcp.resource("agentgit://repositories/{repository_id}/index/status")
def get_index_status_resource(repository_id: str) -> str:
    """Read-only status of the codebase index."""
    db = _get_db()
    try:
        indexer = CodebaseIndexer(db)
        status = indexer.get_index_status(repository_id)
        return json.dumps(status.model_dump(), indent=2, default=str)
    finally:
        _close_db(db)


import logging

def run_server():
    """CLI Entrypoint for stdio MCP server."""
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr
    )
    logger.info("Starting AgentGit stdio MCP server...")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run_server()
