from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.services.ingestion import IngestionService
from backend.app.schemas.session import SessionCreate, SessionResponse, SessionDetailResponse
from backend.app.schemas.message import MessageBatchCreate, MessageBatchResponse, MessageResponse

router = APIRouter(prefix="/sessions", tags=["Sessions & Ingestion"])


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(session_in: SessionCreate, db: Session = Depends(get_db)):
    ingestion = IngestionService(db)
    session = ingestion.create_session(title=session_in.title)
    return session


@router.get("", response_model=List[SessionResponse])
def list_sessions(db: Session = Depends(get_db)):
    ingestion = IngestionService(db)
    return ingestion.list_sessions()


@router.get("/{session_id}", response_model=SessionDetailResponse)
def get_session(session_id: str, db: Session = Depends(get_db)):
    ingestion = IngestionService(db)
    session = ingestion.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SESSION_NOT_FOUND", "message": f"Session '{session_id}' not found."}
        )
    return session


@router.post("/{session_id}/messages", response_model=MessageBatchResponse, status_code=status.HTTP_201_CREATED)
def ingest_messages(session_id: str, batch: MessageBatchCreate, db: Session = Depends(get_db)):
    ingestion = IngestionService(db)
    try:
        messages = ingestion.ingest_messages(session_id, batch.messages)
        return MessageBatchResponse(session_id=session_id, messages=messages)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SESSION_NOT_FOUND", "message": str(e)}
        )


@router.get("/{session_id}/messages", response_model=List[MessageResponse])
def get_session_messages(session_id: str, db: Session = Depends(get_db)):
    ingestion = IngestionService(db)
    session = ingestion.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SESSION_NOT_FOUND", "message": f"Session '{session_id}' not found."}
        )
    return ingestion.get_session_messages(session_id)

