import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.models.memory import MemoryDecision
from backend.app.schemas.memory import MemoryCandidate, MemoryDecisionOverrideRequest
from backend.app.schemas.common import RetentionAction
from backend.app.providers import get_provider


class RetentionPolicyService:
    def __init__(self, db: Session, policy_version: Optional[str] = None):
        self.db = db
        self.policy_version = policy_version or settings.POLICY_VERSION

    def evaluate_candidate(self, candidate: MemoryCandidate, mode: Optional[str] = None) -> MemoryCandidate:
        provider = get_provider(mode)
        return provider.classify_candidate(candidate)

    def evaluate_all(self, candidates: List[MemoryCandidate], mode: Optional[str] = None) -> List[MemoryCandidate]:
        provider = get_provider(mode)
        evaluated = []
        for cand in candidates:
            evaluated.append(provider.classify_candidate(cand))
        return evaluated

    def record_decisions(
        self,
        candidates: List[MemoryCandidate],
        session_id: Optional[str] = None
    ) -> List[MemoryDecision]:
        decisions: List[MemoryDecision] = []
        for cand in candidates:
            dec = MemoryDecision(
                id=cand.candidate_id or str(uuid.uuid4()),
                session_id=session_id,
                candidate_text=cand.content,
                action=cand.action.value if hasattr(cand.action, "value") else str(cand.action),
                category=cand.category.value if hasattr(cand.category, "value") else str(cand.category),
                topic=cand.topic,
                rationale=cand.rationale,
                source_message_ids=cand.source_message_ids,
                policy_version=self.policy_version,
                user_override=False
            )
            self.db.add(dec)
            decisions.append(dec)

        self.db.commit()
        for d in decisions:
            self.db.refresh(d)
        logger.info(f"Recorded {len(decisions)} memory classification decisions.")
        return decisions

    def apply_override(
        self,
        decision_id: str,
        override_req: MemoryDecisionOverrideRequest
    ) -> MemoryDecision:
        stmt = select(MemoryDecision).where(MemoryDecision.id == decision_id)
        decision = self.db.scalars(stmt).first()
        if not decision:
            # If not in DB yet, create a new record
            action_val = override_req.action.value if hasattr(override_req.action, "value") else str(override_req.action)
            category_val = (
                override_req.category.value if (override_req.category and hasattr(override_req.category, "value"))
                else (str(override_req.category) if override_req.category else "other")
            )
            decision = MemoryDecision(
                id=decision_id,
                candidate_text=override_req.content or "User overridden candidate",
                action=action_val,
                category=category_val,
                topic=override_req.topic or "general",
                rationale=override_req.rationale or "User explicitly overridden decision",
                source_message_ids=override_req.source_message_ids or [],
                policy_version=self.policy_version,
                user_override=True
            )
            self.db.add(decision)
        else:
            decision.action = override_req.action.value if hasattr(override_req.action, "value") else str(override_req.action)
            if override_req.rationale:
                decision.rationale = override_req.rationale
            if override_req.content:
                decision.candidate_text = override_req.content
            if override_req.category:
                decision.category = override_req.category.value if hasattr(override_req.category, "value") else str(override_req.category)
            if override_req.topic:
                decision.topic = override_req.topic
            decision.user_override = True

        self.db.commit()
        self.db.refresh(decision)
        logger.info(f"Applied user override to decision {decision.id}: new_action={decision.action}")
        return decision

