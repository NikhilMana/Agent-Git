from fastapi.testclient import TestClient


def test_full_git_workflow_via_api(client: TestClient):
    # 1. Create Repository
    repo_resp = client.post("/api/v1/repositories", json={"name": "agent-memory-repo"})
    assert repo_resp.status_code == 201
    repo = repo_resp.json()
    repo_id = repo["id"]

    # 2. Initial Commit on main
    commit1_resp = client.post(
        f"/api/v1/repositories/{repo_id}/commits",
        json={
            "branch": "main",
            "message": "Initial architectural baseline",
            "items": [
                {
                    "logical_key": "project.database",
                    "content": "Database is PostgreSQL v16.",
                    "category": "decision",
                    "topic": "database",
                    "source_message_ids": ["msg-1"],
                    "rationale": "Official decision"
                },
                {
                    "logical_key": "architecture.framework",
                    "content": "FastAPI is the REST backend framework.",
                    "category": "decision",
                    "topic": "backend",
                    "source_message_ids": ["msg-2"],
                    "rationale": "API framework"
                }
            ]
        }
    )
    assert commit1_resp.status_code == 201
    c1 = commit1_resp.json()
    c1_id = c1["id"]
    assert len(c1["snapshot_hash"]) == 64
    assert len(c1["items"]) == 2

    # 3. Create branch 'experiment-sqlite'
    branch_resp = client.post(
        f"/api/v1/repositories/{repo_id}/branches",
        json={"name": "experiment-sqlite", "from_commit_id": c1_id}
    )
    assert branch_resp.status_code == 201
    assert branch_resp.json()["name"] == "experiment-sqlite"

    # 4. Commit alternative decision on 'experiment-sqlite'
    commit2_resp = client.post(
        f"/api/v1/repositories/{repo_id}/commits",
        json={
            "branch": "experiment-sqlite",
            "message": "Switch database to SQLite for lightweight local runs",
            "items": [
                {
                    "logical_key": "project.database",
                    "content": "Database is SQLite local file.",
                    "category": "decision",
                    "topic": "database",
                    "source_message_ids": ["msg-3"],
                    "rationale": "Testing alternative"
                },
                {
                    "logical_key": "feature.caching",
                    "content": "Use in-memory LRU cache.",
                    "category": "decision",
                    "topic": "backend",
                    "source_message_ids": ["msg-4"],
                    "rationale": "Cache performance"
                }
            ]
        }
    )
    assert commit2_resp.status_code == 201
    c2 = commit2_resp.json()
    c2_id = c2["id"]

    # 5. Check History of main - should ONLY have c1
    main_hist_resp = client.get(f"/api/v1/repositories/{repo_id}/branches/main/history")
    assert main_hist_resp.status_code == 200
    assert len(main_hist_resp.json()["commits"]) == 1
    assert main_hist_resp.json()["commits"][0]["id"] == c1_id

    # 6. Diff commits
    diff_resp = client.get(f"/api/v1/commits/{c1_id}/diff/{c2_id}")
    assert diff_resp.status_code == 200
    diff = diff_resp.json()
    assert len(diff["added_items"]) == 1
    assert len(diff["modified_items"]) == 1
    assert diff["modified_items"][0]["key"] == "project.database"

    # 7. Attempt to merge conflicting database decision -> HTTP 409 Conflict
    exp_items = c2["items"]
    db_item = next(i for i in exp_items if i["logical_key"] == "project.database")
    cache_item = next(i for i in exp_items if i["logical_key"] == "feature.caching")

    bad_merge_resp = client.post(
        f"/api/v1/repositories/{repo_id}/merge",
        json={
            "source_branch": "experiment-sqlite",
            "target_branch": "main",
            "selected_memory_item_ids": [db_item["memory_item_id"]],
            "message": "Try to overwrite main DB without resolution"
        }
    )
    assert bad_merge_resp.status_code == 409
    conflict_json = bad_merge_resp.json()
    assert conflict_json["error"]["code"] == "MERGE_CONFLICT"
    assert len(conflict_json["conflicts"]) == 1

    # 8. Merge non-conflicting item (cache_item) -> Clean merge with 2 parents!
    good_merge_resp = client.post(
        f"/api/v1/repositories/{repo_id}/merge",
        json={
            "source_branch": "experiment-sqlite",
            "target_branch": "main",
            "selected_memory_item_ids": [cache_item["memory_item_id"]],
            "message": "Merge caching feature into main"
        }
    )
    assert good_merge_resp.status_code == 200
    merge_commit = good_merge_resp.json()
    assert len(merge_commit["parent_commit_ids"]) == 2
    assert c1_id in merge_commit["parent_commit_ids"]
    assert c2_id in merge_commit["parent_commit_ids"]

    # 9. Restore historical snapshot c1 to main -> creates new commit
    restore_resp = client.post(
        f"/api/v1/repositories/{repo_id}/branches/main/restore",
        json={"commit_id": c1_id, "message": "Rollback main to pristine commit 1"}
    )
    assert restore_resp.status_code == 200
    restored = restore_resp.json()
    assert restored["snapshot_hash"] == c1["snapshot_hash"]
    assert restored["id"] != c1_id

    # 10. Retrieval test
    retrieval_resp = client.post(
        f"/api/v1/repositories/{repo_id}/retrieve",
        json={
            "query": "Which database is used?",
            "branch": "main",
            "top_k": 5
        }
    )
    assert retrieval_resp.status_code == 200
    r_data = retrieval_resp.json()
    assert len(r_data["results"]) > 0
    assert "postgresql" in r_data["results"][0]["content"].lower()
    assert "msg-1" in r_data["results"][0]["source_message_ids"]

