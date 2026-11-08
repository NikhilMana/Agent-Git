from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.services.retrieval import RetrievalService
from backend.app.services.audit_service import AuditService
from backend.app.schemas.retrieval import RetrievalRequest, RetrievalResponse

router = APIRouter(tags=["Retrieval"])


@router.post("/repositories/{repository_id}/retrieve", response_model=RetrievalResponse)
def retrieve_memory(
    repository_id: str,
    retrieval_in: RetrievalRequest,
    db: Session = Depends(get_db)
):
    retrieval_svc = RetrievalService(db)
    audit_svc = AuditService(db)

    try:
        response = retrieval_svc.retrieve(
            repository_id=repository_id,
            query=retrieval_in.query,
            branch_name=retrieval_in.branch or "main",
            top_k=retrieval_in.top_k or 5
        )

        audit_svc.record_event(
            "retrieve",
            payload={
                "repository_id": repository_id,
                "query": retrieval_in.query,
                "branch": retrieval_in.branch,
                "results_count": len(response.results)
            }
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "RETRIEVAL_ERROR", "message": str(e)}
        )

