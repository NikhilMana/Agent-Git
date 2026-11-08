from fastapi.testclient import TestClient


def test_session_lifecycle_and_message_ingestion(client: TestClient):
    # 1. Create session
    create_resp = client.post("/api/v1/sessions", json={"title": "Test AI Project"})
    assert create_resp.status_code == 201
    session_data = create_resp.json()
    session_id = session_data["id"]
    assert session_data["title"] == "Test AI Project"

    # 2. Ingest messages
    messages = [
        {"role": "user", "content": "Use FastAPI and PostgreSQL for the backend."},
        {"role": "assistant", "content": "Understood. I will use that stack."}
    ]
    ingest_resp = client.post(f"/api/v1/sessions/{session_id}/messages", json={"messages": messages})
    assert ingest_resp.status_code == 201
    ingest_data = ingest_resp.json()
    assert len(ingest_data["messages"]) == 2
    msg_id1 = ingest_data["messages"][0]["id"]

    # 3. Get session messages
    get_msgs_resp = client.get(f"/api/v1/sessions/{session_id}/messages")
    assert get_msgs_resp.status_code == 200
    msgs = get_msgs_resp.json()
    assert len(msgs) == 2
    assert msgs[0]["id"] == msg_id1

    # 4. Error response when session does not exist
    bad_resp = client.post("/api/v1/sessions/non-existent-id/messages", json={"messages": messages})
    assert bad_resp.status_code == 404
    assert "error" in bad_resp.json()
    assert bad_resp.json()["error"]["code"] == "SESSION_NOT_FOUND"

