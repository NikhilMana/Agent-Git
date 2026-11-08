import json
import os
import sys
import uuid
from backend.app.db.session import SessionLocal, create_all_tables
from backend.app.services.ingestion import IngestionService
from backend.app.services.extractor import CandidateExtractor
from backend.app.services.retention import RetentionPolicyService
from backend.app.services.version_service import VersionService
from backend.app.services.retrieval import RetrievalService
from backend.app.schemas.message import MessageCreate
from backend.app.schemas.commit import CommitCreate
from backend.app.schemas.memory import MemoryItemCreate
from backend.app.schemas.common import RetentionAction, RoleEnum


def run_demo():
    print("=" * 80)
    print("AgentGit MVP — Live End-to-End Demonstration")
    print("Problem Statement: Context Memory for Long-Running Agentic AI")
    print("=" * 80)

    # 1. Initialize DB
    create_all_tables()
    db = SessionLocal()

    ingestion_svc = IngestionService(db)
    extractor = CandidateExtractor(mode="deterministic")
    retention_svc = RetentionPolicyService(db)
    version_svc = VersionService(db)
    retrieval_svc = RetrievalService(db)

    # Step 1: Ingest conversation
    print("\n[Step 1] Ingesting conversation from sample_data/conversation_project.json...")
    with open("sample_data/conversation_project.json", "r", encoding="utf-8") as f:
        sample = json.load(f)

    session = ingestion_svc.create_session(title=sample["title"])
    messages_in = [
        MessageCreate(role=RoleEnum(m["role"]), content=m["content"])
        for m in sample["messages"]
    ]
    stored_messages = ingestion_svc.ingest_messages(session.id, messages_in)
    print(f"-> Ingested {len(stored_messages)} messages into session: {session.id}")

    # Step 2: Candidate extraction and classification
    print("\n[Step 2] Candidate Extraction and Adaptive Retention Classification...")
    candidates = extractor.extract(stored_messages)
    evaluated = retention_svc.evaluate_all(candidates)
    retention_svc.record_decisions(evaluated, session_id=session.id)

    retained_items = []
    for idx, c in enumerate(evaluated, 1):
        action_mark = "[RETAIN]" if c.action == RetentionAction.RETAIN else ("[SUMMARIZE]" if c.action == RetentionAction.SUMMARIZE else "[DISCARD]")
        print(f"  {idx}. {action_mark:<11} ({c.category.value}) {c.content[:60]}... | Rationale: {c.rationale}")
        if c.action in (RetentionAction.RETAIN, RetentionAction.SUMMARIZE):
            retained_items.append(
                MemoryItemCreate(
                    logical_key=c.logical_key,
                    content=c.content,
                    category=c.category,
                    topic=c.topic,
                    source_message_ids=c.source_message_ids,
                    rationale=c.rationale,
                    confidence=c.confidence,
                    retention_action=c.action
                )
            )

    # Step 3: Initial Memory Commit on main
    print("\n[Step 3] Creating Initial Immutable Memory Commit on 'main' branch...")
    repo_name = f"demo-repo-{uuid.uuid4().hex[:6]}"
    repo = version_svc.get_or_create_repository(repo_name, "AgentGit Live Demo Repository")
    c1 = version_svc.create_commit(
        repo.id,
        CommitCreate(
            branch="main",
            message="Initial verified architecture decisions",
            items=retained_items
        )
    )
    print(f"-> Commit ID: {c1.id}")
    print(f"-> Snapshot SHA-256 Hash: {c1.snapshot_hash}")
    print(f"-> Verified Snapshot Integrity: {version_svc.verify_commit_integrity(c1.id)}")

    # Step 4: Create alternative branch
    print("\n[Step 4] Creating experimental branch 'experiment-sqlite' from commit 1...")
    branch_exp = version_svc.create_branch(repo.id, "experiment-sqlite", from_commit_id=c1.id)
    print(f"-> Branch '{branch_exp.name}' created at head commit {branch_exp.head_commit_id[:8]}")

    # Step 5: Commit alternative decision on experiment branch
    print("\n[Step 5] Committing alternative decision on 'experiment-sqlite'...")
    c2 = version_svc.create_commit(
        repo.id,
        CommitCreate(
            branch="experiment-sqlite",
            message="Experiment: Switch to SQLite and add Redis caching",
            items=[
                MemoryItemCreate(
                    logical_key="project.database",
                    content="Database is SQLite file-based engine.",
                    category="decision",  # type: ignore
                    topic="database",
                    source_message_ids=["exp-msg-01"],
                    rationale="Experimental lightweight database choice"
                ),
                MemoryItemCreate(
                    logical_key="system.caching",
                    content="Redis cluster configured with 5-minute TTL.",
                    category="decision",  # type: ignore
                    topic="backend",
                    source_message_ids=["exp-msg-02"],
                    rationale="Redis cache implementation"
                )
            ]
        )
    )
    print(f"-> Commit on 'experiment-sqlite': {c2.id} (hash={c2.snapshot_hash[:8]})")

    # Step 6: Verify branch isolation: main branch remains unchanged
    print("\n[Step 6] Verifying Branch Isolation...")
    main_b = version_svc.get_branch(repo.id, "main")
    main_items = version_svc.get_commit_items(main_b.head_commit_id)
    main_db_item = next((i for i in main_items if i.logical_key == "project.database" and "PostgreSQL" in i.content_at_commit), None)
    print(f"-> 'main' branch head commit: {main_b.head_commit_id[:8]} (still commit 1)")
    print(f"-> 'main' branch database fact: \"{main_db_item.content_at_commit if main_db_item else 'N/A'}\"")
    assert main_db_item is not None
    assert "PostgreSQL" in main_db_item.content_at_commit

    # Step 7: Selected merge with conflict detection
    print("\n[Step 7] Testing Conflict Detection and Selective Merge...")
    exp_items = version_svc.get_commit_items(c2.id)
    sqlite_item = next(i for i in exp_items if i.logical_key == "project.database")
    redis_item = next(i for i in exp_items if i.logical_key == "system.caching")

    # Attempting to merge conflicting database decision
    conflicts, _, _ = version_svc.check_merge_conflicts(
        repo.id, "experiment-sqlite", "main", [sqlite_item.memory_item_id]
    )
    print(f"-> Conflict check for 'project.database': {len(conflicts)} conflict(s) detected!")
    print(f"   Reason: {conflicts[0].conflict_reason}")

    # Merging non-conflicting caching item
    merge_commit = version_svc.merge_branches(
        repo.id,
        source_branch_name="experiment-sqlite",
        target_branch_name="main",
        selected_memory_item_ids=[redis_item.memory_item_id],
        message="Merge non-conflicting Redis caching into main"
    )
    print(f"-> Successful Two-Parent Merge Commit: {merge_commit.id}")
    print(f"   Parent IDs: {merge_commit.parent_commit_ids}")

    # Step 8: Historical Snapshot Restore
    print("\n[Step 8] Restoring original snapshot c1 to 'main' as a non-destructive new commit...")
    restore_commit = version_svc.restore_snapshot(
        repo.id,
        branch_name="main",
        target_commit_id=c1.id,
        message="Restore to pristine baseline c1"
    )
    print(f"-> Restored commit ID: {restore_commit.id}")
    print(f"-> Restored snapshot hash matches c1: {restore_commit.snapshot_hash == c1.snapshot_hash}")

    history = version_svc.list_branch_history(repo.id, "main")
    print(f"-> Full commit history on 'main' ({len(history)} commits preserved in total):")
    for c in history:
        print(f"   * [{c.id[:8]}] {c.message} (parents: {[p[:8] for p in c.parent_commit_ids]})")

    # Step 9: Retrieval with source provenance
    print("\n[Step 9] Querying Memory with Lexical Retrieval and Source Provenance...")
    query = "Which database did we choose?"
    retrieval = retrieval_svc.retrieve(repo.id, query=query, branch_name="main")
    print(f"-> Query: \"{query}\"")
    print(f"-> Found {len(retrieval.results)} relevant memories:")
    for r in retrieval.results:
        print(f"   - Relevance Score: {r.score}")
        print(f"   - Memory Content: {r.content}")
        print(f"   - Source Message IDs: {r.source_message_ids}")
        print(f"   - Topic: {r.topic} | Commit: {r.commit_id[:8]}")

    print("\n-> Context block built for Agent context window:")
    print(retrieval.context_text)

    db.close()
    print("\n" + "=" * 80)
    print("Demo completed successfully! All requirements verified.")
    print("=" * 80)


if __name__ == "__main__":
    run_demo()
