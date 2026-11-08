from typing import List, Optional
import httpx
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.models.message import Message
from backend.app.schemas.memory import MemoryCandidate
from backend.app.providers.base import BaseModelProvider
from backend.app.providers.deterministic import DeterministicProvider


class OllamaProvider(BaseModelProvider):
    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.fallback = DeterministicProvider()

    def is_available(self) -> bool:
        try:
            with httpx.Client(timeout=1.5) as client:
                res = client.get(f"{self.base_url}/api/tags")
                return res.status_code == 200
        except Exception:
            return False

    def extract_candidates(self, messages: List[Message]) -> List[MemoryCandidate]:
        # Always safe fallback if Ollama is unreachable
        if not self.is_available():
            logger.info("Ollama unavailable, falling back to DeterministicProvider for extraction.")
            return self.fallback.extract_candidates(messages)

        # For MVP, deterministic extraction is reliable and can be supplemented by LLM
        return self.fallback.extract_candidates(messages)

    def classify_candidate(self, candidate: MemoryCandidate) -> MemoryCandidate:
        if not self.is_available():
            return self.fallback.classify_candidate(candidate)

        # In LLM mode, can prompt Ollama, but fall back gracefully
        try:
            prompt = (
                f"Classify this candidate text for long-term agent memory into retain, summarize, or discard.\n"
                f"Candidate: {candidate.content}\n"
                f"Reply with action, category, and a one sentence rationale."
            )
            with httpx.Client(timeout=5.0) as client:
                res = client.post(
                    f"{self.base_url}/api/generate",
                    json={"model": self.model, "prompt": prompt, "stream": False}
                )
                if res.status_code == 200:
                    # Ollama answered
                    pass
        except Exception as e:
            logger.warning(f"Ollama call failed ({e}), using deterministic classifier.")

        return self.fallback.classify_candidate(candidate)

    def summarize_text(self, text: str, preserve_entities: Optional[List[str]] = None) -> str:
        if not self.is_available():
            return self.fallback.summarize_text(text, preserve_entities)

        try:
            prompt = (
                f"Compress the following text into a concise summary while strictly preserving all "
                f"dates, version numbers, technical names, and negations:\n{text}"
            )
            with httpx.Client(timeout=8.0) as client:
                res = client.post(
                    f"{self.base_url}/api/generate",
                    json={"model": self.model, "prompt": prompt, "stream": False}
                )
                if res.status_code == 200:
                    resp_data = res.json()
                    summary = resp_data.get("response", "").strip()
                    if summary:
                        return summary
        except Exception as e:
            logger.warning(f"Ollama summarization failed ({e}), falling back to deterministic.")

        return self.fallback.summarize_text(text, preserve_entities)

    def get_embedding(self, text: str) -> Optional[List[float]]:
        if not self.is_available():
            return None
        try:
            with httpx.Client(timeout=3.0) as client:
                res = client.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": self.model, "prompt": text}
                )
                if res.status_code == 200:
                    return res.json().get("embedding")
        except Exception:
            pass
        return None

