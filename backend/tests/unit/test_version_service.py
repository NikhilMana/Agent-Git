import pytest
from sqlalchemy.orm import Session
from backend.app.services.version_service import VersionService
from backend.app.schemas.commit import CommitCreate
from backend.app.schemas.memory import MemoryItemCreate
from backend.app.schemas.common import MemoryCategory, RetentionAction


def test_commit_creation_and_snapshot_immutability(db_session: Session):
    service = VersionService(db_session)
    repo = service.get_or_create_repository("test-repo")

    commit_data = CommitCreate(
        branch="main",
        message="Initial commit",
        items=[
            MemoryItemCreate(
                logical_key="project.database",
                content="Use PostgreSQL for the primary store.",
                category=MemoryCategory.DECISION,
                topic="database",
                source_message_ids=["m-01"],
                rationale="Architectural agreement."
            )
        ]
    )

    commit = service.create_commit(repo.id, commit_data)
    assert commit.id is not None
    assert commit.snapshot_hash is not None
    assert service.verify_commit_integrity(commit.id) is True

    # Check history
    history = service.list_branch_history(repo.id, "main")
    assert len(history) == 1
    assert history[0].id == commit.id


def test_branch_isolation(db_session: Session):
    service = VersionService(db_session)
    repo = service.get_or_create_repository("branch-repo")

    # Commit 1 on main
    c1 = service.create_commit(
        repo.id,
        CommitCreate(
            branch="main",
            message="Initial on main",
            items=[
                MemoryItemCreate(
                    logical_key="project.database",
                    content="Database is PostgreSQL.",
                    category=MemoryCategory.DECISION,
                    topic="database",
                    source_message_ids=["m-1"],
                    rationale="Chosen DB"
                )
            ]
        )
    )

    # Branch experiment-sqlite from c1
    branch_exp = service.create_branch(repo.id, "experiment-sqlite", from_commit_id=c1.id)
    assert branch_exp.head_commit_id == c1.id

    # Commit c2 on experiment-sqlite with different database
    c2 = service.create_commit(
        repo.id,
        CommitCreate(
            branch="experiment-sqlite",
            message="Switch to SQLite for testing",
            items=[
                MemoryItemCreate(
                    logical_key="project.database",
                    content="Database is SQLite in-memory.",
                    category=MemoryCategory.DECISION,
                    topic="database",
                    source_message_ids=["m-2"],
                    rationale="Test plan"
                )
            ]
        )
    )

    # Verify main branch head is STILL c1 and its items remain unchanged
    main_b = service.get_branch(repo.id, "main")
    assert main_b.head_commit_id == c1.id
    main_items = service.get_commit_items(c1.id)
    assert len(main_items) == 1
    assert main_items[0].content_at_commit == "Database is PostgreSQL."

    # Verify experiment branch has c2
    exp_b = service.get_branch(repo.id, "experiment-sqlite")
    assert exp_b.head_commit_id == c2.id
    exp_items = service.get_commit_items(c2.id)
    assert exp_items[0].content_at_commit == "Database is SQLite in-memory."


def test_restore_equivalence_and_non_destructive_history(db_session: Session):
    service = VersionService(db_session)
    repo = service.get_or_create_repository("restore-repo")

    # Commit 1
    c1 = service.create_commit(
        repo.id,
        CommitCreate(
            branch="main",
            message="Commit 1",
            items=[
                MemoryItemCreate(
                    logical_key="key1",
                    content="Version 1 content",
                    category=MemoryCategory.FACT,
                    topic="general",
                    source_message_ids=["m-1"],
                    rationale="Initial"
                )
            ]
        )
    )

    # Commit 2 (changes key1)
    c2 = service.create_commit(
        repo.id,
        CommitCreate(
            branch="main",
            message="Commit 2",
            items=[
                MemoryItemCreate(
                    logical_key="key1",
                    content="Version 2 content",
                    category=MemoryCategory.FACT,
                    topic="general",
                    source_message_ids=["m-2"],
                    rationale="Updated"
                )
            ]
        )
    )

    # Restore c1 as a new commit
    c3 = service.restore_snapshot(repo.id, "main", c1.id, message="Restore snapshot 1")
    assert c3.id != c1.id
    assert c3.id != c2.id
    assert c3.snapshot_hash == c1.snapshot_hash  # Same content state!

    # Verify history contains all 3 commits in order (c3 -> c2 -> c1)
    history = service.list_branch_history(repo.id, "main")
    assert len(history) == 3
    assert history[0].id == c3.id
    assert history[1].id == c2.id
    assert history[2].id == c1.id


def test_merge_selected_items_and_conflict_detection(db_session: Session):
    service = VersionService(db_session)
    repo = service.get_or_create_repository("merge-repo")

    # Main has database = Postgres
    c_main = service.create_commit(
        repo.id,
        CommitCreate(
            branch="main",
            message="Main init",
            items=[
                MemoryItemCreate(
                    logical_key="project.database",
                    content="Database is PostgreSQL.",
                    category=MemoryCategory.DECISION,
                    topic="database",
                    source_message_ids=["m-1"],
                    rationale="Primary store"
                )
            ]
        )
    )

    # Branch feature-auth has new auth fact AND conflicting database = SQLite
    b_auth = service.create_branch(repo.id, "feature-auth", from_commit_id=c_main.id)
    c_auth = service.create_commit(
        repo.id,
        CommitCreate(
            branch="feature-auth",
            message="Add auth and change DB",
            items=[
                MemoryItemCreate(
                    logical_key="system.auth",
                    content="Authentication uses JWT RS256.",
                    category=MemoryCategory.DECISION,
                    topic="security",
                    source_message_ids=["m-auth"],
                    rationale="JWT tokens"
                ),
                MemoryItemCreate(
                    logical_key="project.database",
                    content="Database is SQLite in file.",
                    category=MemoryCategory.DECISION,
                    topic="database",
                    source_message_ids=["m-db2"],
                    rationale="Changed DB"
                )
            ]
        )
    )

    auth_items = service.get_commit_items(c_auth.id)
    auth_jwt_item = next(i for i in auth_items if i.logical_key == "system.auth")
    auth_db_item = next(i for i in auth_items if i.logical_key == "project.database")

    # Test 1: Selecting the conflicting DB item triggers conflict
    conflicts, _, _ = service.check_merge_conflicts(
        repo.id, "feature-auth", "main", [auth_db_item.memory_item_id]
    )
    assert len(conflicts) == 1
    assert conflicts[0].logical_key == "project.database"

    # Test 2: Selecting non-conflicting auth item merges cleanly with 2 parents!
    merge_commit = service.merge_branches(
        repo.id,
        source_branch_name="feature-auth",
        target_branch_name="main",
        selected_memory_item_ids=[auth_jwt_item.memory_item_id],
        message="Merge auth item"
    )

    assert len(merge_commit.parent_commit_ids) == 2
    assert c_main.id in merge_commit.parent_commit_ids
    assert c_auth.id in merge_commit.parent_commit_ids

    # Merged snapshot has both original Postgres AND new auth!
    merged_items = service.get_commit_items(merge_commit.id)
    keys = {i.logical_key for i in merged_items}
    assert "project.database" in keys
    assert "system.auth" in keys

