# AgentGit — API Specification (MVP)

Base path: `/api/v1`

## 1. Health

`GET /health`

Response:
```json
{"status": "ok", "service": "agentgit"}
```

## 2. Create session and ingest messages

`POST /sessions`

Request:
```json
{"title": "Demo project"}
```

`POST /sessions/{session_id}/messages`

Request:
```json
{
  "messages": [
    {"role": "user", "content": "Use FastAPI and PostgreSQL for the backend."},
    {"role": "assistant", "content": "Understood. I will use that stack."}
  ]
}
```

Response includes stored message IDs.

## 3. Generate memory candidates

`POST /sessions/{session_id}/memory/preview`

Request:
```json
{"mode": "deterministic"}
```

Response:
```json
{
  "candidates": [
    {
      "candidate_id": "candidate-1",
      "content": "Use FastAPI and PostgreSQL for the backend.",
      "action": "retain",
      "category": "decision",
      "topic": "architecture",
      "source_message_ids": ["message-1"],
      "rationale": "Explicit technical decision."
    }
  ]
}
```

## 4. Commit reviewed memory

`POST /repositories/{repository_id}/commits`

Request:
```json
{
  "branch": "main",
  "message": "Initial memory commit",
  "items": [
    {
      "content": "Use FastAPI and PostgreSQL.",
      "category": "decision",
      "topic": "architecture",
      "source_message_ids": ["message-1"],
      "rationale": "Explicit user decision."
    }
  ]
}
```

## 5. History and snapshot

- `GET /repositories/{repository_id}/branches`
- `GET /repositories/{repository_id}/branches/{branch_name}/history`
- `GET /commits/{commit_id}`
- `GET /commits/{commit_id}/diff/{other_commit_id}`

## 6. Branch and restore

`POST /repositories/{repository_id}/branches`

Request:
```json
{"name": "experiment-db", "from_commit_id": "commit-1"}
```

`POST /branches/{branch_name}/restore`

Request:
```json
{"commit_id": "commit-1", "message": "Restore known-good memory"}
```

Restore must create a new commit on the branch.

## 7. Merge

`POST /repositories/{repository_id}/merge`

Request:
```json
{
  "source_branch": "experiment-db",
  "target_branch": "main",
  "selected_memory_item_ids": ["memory-2"],
  "message": "Merge selected database decision"
}
```

If conflicting logical keys exist, return a conflict response requiring explicit resolution.

## 8. Retrieval

`POST /repositories/{repository_id}/retrieve`

Request:
```json
{
  "query": "Which database did we choose?",
  "branch": "main",
  "top_k": 5
}
```

Response includes content, score, source message IDs, topic, and commit ID.

## 9. Error format

```json
{
  "error": {
    "code": "COMMIT_NOT_FOUND",
    "message": "The requested commit does not exist."
  }
}
```

Use appropriate HTTP status codes: 400 invalid request, 404 missing resource, 409 merge conflict, 422 validation failure, 500 unexpected server error.
