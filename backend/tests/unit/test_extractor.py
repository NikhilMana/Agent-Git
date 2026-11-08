import uuid
from backend.app.models.message import Message
from backend.app.services.extractor import CandidateExtractor
from backend.app.schemas.common import RetentionAction, MemoryCategory


def test_classify_filler_and_greetings():
    extractor = CandidateExtractor(mode="deterministic")
    msg1 = Message(id="m-1", session_id="s-1", role="user", content="Hello! Good morning.")
    msg2 = Message(id="m-2", session_id="s-1", role="assistant", content="Thanks, sounds good!")

    candidates = extractor.extract([msg1, msg2])
    assert len(candidates) >= 2
    for c in candidates:
        assert c.action == RetentionAction.DISCARD
        assert "filler" in c.rationale.lower() or "greeting" in c.rationale.lower()


def test_classify_negation_and_constraints():
    extractor = CandidateExtractor(mode="deterministic")
    msg = Message(
        id="m-3",
        session_id="s-1",
        role="user",
        content="We must never expose database secrets. Do not use plain text passwords."
    )
    candidates = extractor.extract([msg])
    assert len(candidates) >= 1
    for c in candidates:
        assert c.action == RetentionAction.RETAIN
        assert c.category == MemoryCategory.CONSTRAINT
        assert "constraint" in c.rationale.lower() or "negation" in c.rationale.lower()
        assert "m-3" in c.source_message_ids


def test_classify_explicit_decisions():
    extractor = CandidateExtractor(mode="deterministic")
    msg = Message(
        id="m-4",
        session_id="s-1",
        role="user",
        content="We decided to use FastAPI and PostgreSQL for the backend service."
    )
    candidates = extractor.extract([msg])
    assert len(candidates) == 1
    c = candidates[0]
    assert c.action == RetentionAction.RETAIN
    assert c.category == MemoryCategory.DECISION
    assert c.logical_key in ["architecture.backend_framework", "project.database"]
    assert "m-4" in c.source_message_ids


def test_classify_dates_identifiers_and_numbers():
    extractor = CandidateExtractor(mode="deterministic")
    msg = Message(
        id="m-5",
        session_id="s-1",
        role="user",
        content="The server runs on port 8000 and the release deadline is 2026-12-31 with v2.1.0."
    )
    candidates = extractor.extract([msg])
    assert len(candidates) == 1
    c = candidates[0]
    assert c.action == RetentionAction.RETAIN
    assert c.category == MemoryCategory.FACT
    assert "numeric" in c.rationale.lower() or "version" in c.rationale.lower() or "identifier" in c.rationale.lower()
    assert "m-5" in c.source_message_ids


def test_classify_user_preferences():
    extractor = CandidateExtractor(mode="deterministic")
    msg = Message(
        id="m-6",
        session_id="s-1",
        role="user",
        content="I prefer dark mode UI and concise logging."
    )
    candidates = extractor.extract([msg])
    assert len(candidates) == 1
    c = candidates[0]
    assert c.action == RetentionAction.RETAIN
    assert c.category == MemoryCategory.PREFERENCE


def test_classify_verbose_explanation():
    extractor = CandidateExtractor(mode="deterministic")
    msg = Message(
        id="m-7",
        session_id="s-1",
        role="assistant",
        content=(
            "When designing a distributed event-driven system with high throughput, "
            "it is often beneficial to separate command models from read models using CQRS "
            "because reads and writes have very different scaling profiles, latency requirements, "
            "and consistency boundaries across microservice components."
        )
    )
    candidates = extractor.extract([msg])
    assert len(candidates) == 1
    c = candidates[0]
    assert c.action == RetentionAction.SUMMARIZE
    assert c.category == MemoryCategory.SUMMARY
    assert "verbose" in c.rationale.lower()

