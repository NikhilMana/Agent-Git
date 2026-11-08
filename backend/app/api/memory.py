from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.services.ingestion import IngestionService
from backend.app.services.extractor import CandidateExtractor
from backend.app.services.retention import RetentionPolicyService
from backend.app.schemas.memory import (
    CandidatePreviewRequest,
    CandidatePreviewResponse,
    MemoryDecisionOverrideRequest,
    MemoryItemResponse
)

router = APIRouter(tags=["Memory & Candidates"])


@router.post("/sessions/{session_id}/memory/preview", response_model=CandidatePreviewResponse)
def preview_memory_candidates(
    session_id: str,
    req: Optional[CandidatePreviewRequest] = None,
    db: Session = Depends(get_db)
):
    ingestion = IngestionService(db)
    session = ingestion.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SESSION_NOT_FOUND", "message": f"Session '{session_id}' not found."}
        )

    messages = ingestion.get_session_messages(session_id)
    if not messages:
        return CandidatePreviewResponse(session_id=session_id, candidates=[])

    mode = req.mode if req else "deterministic"
    extractor = CandidateExtractor(mode=mode)
    candidates = extractor.extract(messages, mode=mode)

    retention_svc = RetentionPolicyService(db)
    evaluated = retention_svc.evaluate_all(candidates, mode=mode)

    # Persist the evaluation decisions for traceability
    retention_svc.record_decisions(evaluated, session_id=session_id)

    return CandidatePreviewResponse(session_id=session_id, candidates=evaluated)


@router.post("/memory/decisions/{decision_id}/override")
def override_memory_decision(
    decision_id: str,
    override_req: MemoryDecisionOverrideRequest,
    db: Session = Depends(get_db)
):
    retention_svc = RetentionPolicyService(db)
    decision = retention_svc.apply_override(decision_id, override_req)
    return {
        "status": "overridden",
        "decision_id": decision.id,
        "action": decision.action,
        "user_override": decision.user_override
    }

