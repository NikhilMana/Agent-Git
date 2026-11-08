import uuid
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from backend.app.models.session import ConversationSession
from backend.app.models.message import Message
from backend.app.schemas.message import MessageCreate
from backend.app.core.logging import logger


class IngestionService:
    def __init__(self, db: Session):
        self.db = db

    def create_session(self, title: Optional[str] = None) -> ConversationSession:
        session = ConversationSession(
            id=str(uuid.uuid4()),
            title=title
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        logger.info(f"Created conversation session: {session.id} (title={title})")
        return session

    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        stmt = select(ConversationSession).where(ConversationSession.id == session_id)
        return self.db.scalars(stmt).first()

    def list_sessions(self) -> List[ConversationSession]:
        stmt = select(ConversationSession).order_by(ConversationSession.created_at.desc())
        return list(self.db.scalars(stmt).all())

    def ingest_messages(self, session_id: str, messages_data: List[MessageCreate]) -> List[Message]:
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session with ID '{session_id}' not found.")

        created_messages = []
        for msg in messages_data:
            msg_obj = Message(
                id=str(uuid.uuid4()),
                session_id=session_id,
                role=msg.role.value if hasattr(msg.role, "value") else str(msg.role),
                content=msg.content.strip(),
                metadata_json=msg.metadata_json
            )
            self.db.add(msg_obj)
            created_messages.append(msg_obj)

        self.db.commit()
        for msg_obj in created_messages:
            self.db.refresh(msg_obj)

        logger.info(f"Ingested {len(created_messages)} messages into session: {session_id}")
        return created_messages

    def get_session_messages(self, session_id: str) -> List[Message]:
        stmt = (
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at.asc())
        )
        return list(self.db.scalars(stmt).all())

