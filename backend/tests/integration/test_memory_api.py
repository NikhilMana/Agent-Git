from fastapi.testclient import TestClient


def test_memory_candidate_preview_and_override(client: TestClient):
    # 1. Create session and ingest conversation
    session_resp = client.post("/api/v1/sessions", json={"title": "Architecture Conversation"})
    session_id = session_resp.json()["id"]

    client.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={
            "messages": [
                {"role": "user", "content": "Hi there!"},
                {"role": "assistant", "content": "Hello! How can I help?"},
                {"role": "user", "content": "We decided to use FastAPI and PostgreSQL for the backend."},
                {"role": "user", "content": "Never commit plaintext secret tokens."}
            ]
        }
    )

    # 2. Preview candidates
    preview_resp = client.post(f"/api/v1/sessions/{session_id}/memory/preview", json={"mode": "deterministic"})
    assert preview_resp.status_code == 200
    candidates = preview_resp.json()["candidates"]
    assert len(candidates) >= 3

    # Verify filler discarded and constraints/decisions retained
    actions = [c["action"] for c in candidates]
    assert "discard" in actions
    assert "retain" in actions

    # Find the decision candidate
    decision_cand = next(c for c in candidates if "FastAPI" in c["content"])
    assert decision_cand["action"] == "retain"
    assert decision_cand["category"] == "decision"
    assert len(decision_cand["source_message_ids"]) > 0

    # 3. User override
    override_resp = client.post(
        f"/api/v1/memory/decisions/{decision_cand['candidate_id']}/override",
        json={
            "action": "summarize",
            "rationale": "User preferred to summarize this decision."
        }
    )
    assert override_resp.status_code == 200
    assert override_resp.json()["action"] == "summarize"
    assert override_resp.json()["user_override"] is True

