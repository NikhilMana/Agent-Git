from backend.app.services.version_service import compute_snapshot_hash


def test_snapshot_hash_stability():
    items1 = [
        {
            "logical_key": "project.database",
            "content": "Use PostgreSQL for production.",
            "category": "decision",
            "topic": "database",
            "source_message_ids": ["m-1", "m-2"],
            "retention_action": "retain"
        },
        {
            "logical_key": "architecture.backend_framework",
            "content": "FastAPI is the web framework.",
            "category": "decision",
            "topic": "backend",
            "source_message_ids": ["m-3"],
            "retention_action": "retain"
        }
    ]

    # Same items, reversed order and source IDs permutation
    items2 = [
        {
            "logical_key": "architecture.backend_framework",
            "content": "FastAPI is the web framework.",
            "category": "decision",
            "topic": "backend",
            "source_message_ids": ["m-3"],
            "retention_action": "retain"
        },
        {
            "logical_key": "project.database",
            "content": "Use PostgreSQL for production.",
            "category": "decision",
            "topic": "database",
            "source_message_ids": ["m-2", "m-1"],  # reversed IDs
            "retention_action": "retain"
        }
    ]

    hash1 = compute_snapshot_hash(items1)
    hash2 = compute_snapshot_hash(items2)
    assert hash1 == hash2, "Canonical snapshot hash must be independent of order"
    assert len(hash1) == 64


def test_snapshot_hash_detects_content_change():
    items = [
        {
            "logical_key": "project.database",
            "content": "Use PostgreSQL for production.",
            "category": "decision",
            "topic": "database",
            "source_message_ids": ["m-1"],
            "retention_action": "retain"
        }
    ]
    hash_original = compute_snapshot_hash(items)

    tampered_items = [
        {
            "logical_key": "project.database",
            "content": "Use MySQL for production.",  # changed
            "category": "decision",
            "topic": "database",
            "source_message_ids": ["m-1"],
            "retention_action": "retain"
        }
    ]
    hash_tampered = compute_snapshot_hash(tampered_items)
    assert hash_original != hash_tampered

