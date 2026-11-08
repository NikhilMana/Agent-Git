import re
import uuid
from typing import List, Optional, Tuple
from backend.app.models.message import Message
from backend.app.schemas.memory import MemoryCandidate
from backend.app.schemas.common import RetentionAction, MemoryCategory
from backend.app.providers.base import BaseModelProvider


GREETING_PATTERNS = [
    r"^(hello|hi|hey|hi\s+there|hey\s+there|good\s+(morning|afternoon|evening|day)|greetings)[\s\.,!]*$",
    r"^(how\s+can\s+i\s+help(\s+you)?|how\s+are\s+you|what\s+can\s+i\s+do\s+for\s+you)[\s\.,!\?]*$",
    r"^(thanks|thank\s+you|appreciate\s+it|thx|many\s+thanks)[\s\.,!]*$",
    r"^(okay|ok|sure|sure\s+thing|got\s+it|understood|sounds\s+good|cool|alright|no\s+problem|will\s+do|agreed)[\s\.,!]*$",
    r"^(bye|goodbye|see\s+ya|catch\s+you\s+later|talk\s+soon|see\s+you)[\s\.,!]*$",
    r"^(let\s+me\s+think|wait|brb|hold\s+on|one\s+sec)[\s\.,!]*$",
    r"^(let\'?s\s+(start|begin|discuss|talk))[\s\w\.,!]*$",
]

FILLER_WORDS = {
    "hello", "hi", "hey", "there", "good", "morning", "afternoon", "evening",
    "thanks", "thank", "you", "thx", "appreciate", "it", "okay", "ok", "sure",
    "thing", "sounds", "good", "got", "understood", "cool", "alright", "great",
    "perfect", "no", "problem", "will", "do", "bye", "goodbye", "see", "ya",
    "later", "brb", "wait", "hold", "on", "welcome", "much", "very", "agreed",
    "talk", "soon", "team", "everyone"
}

DECISION_PATTERNS = [
    r"\b(we\s+will\s+use|we\s+shall\s+use|decided\s+to|agreed\s+on|selected|choose|chose|going\s+with|switch\s+to|switched\s+to|settled\s+on)\b",
    r"^(use|adopt|implement)\s+[A-Z0-9][\w\s\+]+(for|as|in)\b",
]

CONSTRAINT_PATTERNS = [
    r"\b(must|cannot|can\s+not|never|prohibit|prohibited|forbidden|only|require|required|do\s+not|don't|should\s+not|strictly)\b",
]

PREFERENCE_PATTERNS = [
    r"\b(prefer|preference|like|prefer\s+to|would\s+rather|priority|favor)\b",
]

TASK_PATTERNS = [
    r"\b(todo|to-do|need\s+to|action\s+item|task:|must\s+fix|will\s+implement|follow\s+up)\b",
]

NUMERIC_OR_IDENTIFIER_PATTERNS = [
    r"\b(v?\d+\.\d+(\.\d+)?)\b",  # version numbers like v1.0.0, 3.11
    r"\b(port\s+\d+|localhost:\d+|:\d{4,5})\b",  # ports
    r"\b(id:\s*[\w\-]+|UUID|sha-?256|[a-f0-9]{32,64})\b",  # IDs or hashes
    r"\b(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4})\b",  # dates
    r"\b(timeout\s*=\s*\d+|limit\s*=\s*\d+|\d+\s*(ms|seconds|minutes|mb|gb|tokens))\b",  # numeric settings
]

TOPIC_KEYWORDS = {
    "database": ["postgres", "postgresql", "sqlite", "mysql", "mongodb", "redis", "database", "sql", "db"],
    "backend": ["fastapi", "flask", "django", "express", "backend", "api", "rest", "server", "python"],
    "frontend": ["react", "vue", "angular", "nextjs", "frontend", "ui", "typescript", "tailwind"],
    "architecture": ["architecture", "monolith", "microservice", "adapter", "pattern", "repository", "layer"],
    "security": ["auth", "token", "jwt", "oauth", "ssl", "tls", "secret", "permission", "security"],
    "model": ["llm", "ollama", "gpt", "gemini", "claude", "embedding", "model", "transformer"],
}

LOGICAL_KEY_MAP = {
    r"\b(postgres|postgresql|sqlite|mysql|mongodb|database|db)\b": "project.database",
    r"\b(fastapi|flask|django|express|backend\s+framework)\b": "architecture.backend_framework",
    r"\b(react|vue|angular|frontend\s+framework)\b": "architecture.frontend_framework",
    r"\b(port\s+\d+|\bport\b)\b": "system.port",
    r"\b(auth|authentication|oauth|jwt)\b": "system.security.auth",
    r"\b(ollama|llama|model|embedding)\b": "system.model_provider",
    r"\b(sqlite)\b": "project.database",
}


class DeterministicProvider(BaseModelProvider):
    def extract_candidates(self, messages: List[Message]) -> List[MemoryCandidate]:
        candidates: List[MemoryCandidate] = []

        for msg in messages:
            content = msg.content.strip()
            if not content:
                continue

            # Split message into sentences or logical paragraphs
            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", content) if s.strip()]
            if not sentences:
                sentences = [content]

            # If the entire message is a greeting or filler
            if self._is_filler(content):
                candidate = MemoryCandidate(
                    candidate_id=str(uuid.uuid4()),
                    content=content,
                    action=RetentionAction.DISCARD,
                    category=MemoryCategory.OTHER,
                    topic="general",
                    source_message_ids=[msg.id],
                    rationale="Greeting, acknowledgment, or transient conversational filler.",
                    confidence=0.99
                )
                candidates.append(candidate)
                continue

            # Process individual sentences / chunks
            for sent in sentences:
                action, category, topic, rationale, key, conf = self._classify_text(sent)
                candidate = MemoryCandidate(
                    candidate_id=str(uuid.uuid4()),
                    logical_key=key,
                    content=sent,
                    action=action,
                    category=category,
                    topic=topic,
                    source_message_ids=[msg.id],
                    rationale=rationale,
                    confidence=conf
                )
                candidates.append(candidate)

        return candidates

    def classify_candidate(self, candidate: MemoryCandidate) -> MemoryCandidate:
        action, category, topic, rationale, key, conf = self._classify_text(candidate.content)
        candidate.action = action
        candidate.category = category
        candidate.topic = topic
        candidate.rationale = rationale
        if key and not candidate.logical_key:
            candidate.logical_key = key
        candidate.confidence = conf
        return candidate

    def summarize_text(self, text: str, preserve_entities: Optional[List[str]] = None) -> str:
        # Deterministic extractive summarizer: keeps key sentences with constraints, decisions, facts
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]
        if len(sentences) <= 1:
            return text.strip()

        scored = []
        for s in sentences:
            score = 0
            if any(re.search(p, s, re.IGNORECASE) for p in CONSTRAINT_PATTERNS):
                score += 5
            if any(re.search(p, s, re.IGNORECASE) for p in DECISION_PATTERNS):
                score += 4
            if any(re.search(p, s, re.IGNORECASE) for p in NUMERIC_OR_IDENTIFIER_PATTERNS):
                score += 3
            if preserve_entities:
                for ent in preserve_entities:
                    if ent.lower() in s.lower():
                        score += 3
            scored.append((score, s))

        # Sort by score descending and pick top 2, then reorder in original order
        top_sentences = sorted(sorted(scored, key=lambda x: x[0], reverse=True)[:2], key=lambda x: sentences.index(x[1]))
        summary = " ".join([s[1] for s in top_sentences])
        return summary if summary else sentences[0]

    def get_embedding(self, text: str) -> Optional[List[float]]:
        # Deterministic fallback does not compute dense neural embeddings
        return None

    def _is_filler(self, text: str) -> bool:
        cleaned = text.strip().lower()
        if len(cleaned) < 2:
            return True
        for pattern in GREETING_PATTERNS:
            if re.match(pattern, cleaned, re.IGNORECASE):
                return True

        # Check if words are entirely composed of filler vocabulary
        words = re.findall(r"\b\w+\b", cleaned)
        if words and all(w in FILLER_WORDS for w in words):
            return True

        return False

    def _classify_text(self, text: str) -> Tuple[RetentionAction, MemoryCategory, str, str, Optional[str], float]:
        lower = text.lower()

        # Check for filler / greetings first
        if self._is_filler(text):
            return (
                RetentionAction.DISCARD,
                MemoryCategory.OTHER,
                "general",
                "Greeting, acknowledgment, or transient conversational filler.",
                None,
                0.95
            )

        # Check for important negation and constraints
        is_negation_or_constraint = any(re.search(p, text, re.IGNORECASE) for p in CONSTRAINT_PATTERNS)
        is_decision = any(re.search(p, text, re.IGNORECASE) for p in DECISION_PATTERNS)
        is_preference = any(re.search(p, text, re.IGNORECASE) for p in PREFERENCE_PATTERNS)
        is_task = any(re.search(p, text, re.IGNORECASE) for p in TASK_PATTERNS)
        has_exact_fact = any(re.search(p, text, re.IGNORECASE) for p in NUMERIC_OR_IDENTIFIER_PATTERNS)

        # Derive topic
        topic = "general"
        for t, keywords in TOPIC_KEYWORDS.items():
            if any(kw in lower for kw in keywords):
                topic = t
                break

        # Derive logical key
        logical_key = None
        for pattern, key in LOGICAL_KEY_MAP.items():
            if re.search(pattern, text, re.IGNORECASE):
                logical_key = key
                break

        # Decision rule 1: Constraints and Negations
        if is_negation_or_constraint:
            return (
                RetentionAction.RETAIN,
                MemoryCategory.CONSTRAINT,
                topic,
                "Explicit constraint or critical negation must be retained verbatim.",
                logical_key,
                0.98
            )

        # Decision rule 2: Explicit Decisions
        if is_decision:
            return (
                RetentionAction.RETAIN,
                MemoryCategory.DECISION,
                topic,
                "Explicit architectural or project decision must be preserved.",
                logical_key,
                0.95
            )

        # Decision rule 3: Exact facts, versions, dates, identifiers
        if has_exact_fact:
            return (
                RetentionAction.RETAIN,
                MemoryCategory.FACT,
                topic,
                "Contains exact numeric value, identifier, date, or version specification.",
                logical_key,
                0.92
            )

        # Decision rule 4: Preferences
        if is_preference:
            return (
                RetentionAction.RETAIN,
                MemoryCategory.PREFERENCE,
                topic,
                "User or team preference recorded for long-term consistency.",
                logical_key,
                0.90
            )

        # Decision rule 5: Unresolved tasks
        if is_task:
            return (
                RetentionAction.RETAIN,
                MemoryCategory.TASK,
                topic,
                "Unresolved task or actionable next step.",
                logical_key,
                0.88
            )

        # Decision rule 6: Long, verbose explanatory text
        word_count = len(text.split())
        if word_count > 30:
            return (
                RetentionAction.SUMMARIZE,
                MemoryCategory.SUMMARY,
                topic,
                "Verbose explanation or background context suitable for compression.",
                logical_key,
                0.85
            )

        # Decision rule 7: Default fallback: retain if uncertain to avoid loss of context
        return (
            RetentionAction.RETAIN,
            MemoryCategory.FACT,
            topic,
            "Domain fact or contextual detail; retained by default safety policy.",
            logical_key,
            0.75
        )
