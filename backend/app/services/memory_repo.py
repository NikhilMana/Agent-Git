import uuid
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from backend.app.models.memory import MemoryItem
from backend.app.schemas.memory import MemoryItemCreate
from backend.app.schemas.common import RetentionAction


class MemoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_item(
        self,
        item_data: MemoryItemCreate,
        repository_id: Optional[str] = None,
        supersedes_item_id: Optional[str] = None
    ) -> MemoryItem:
        action_str = (
            item_data.retention_action.value
            if (item_data.retention_action and hasattr(item_data.retention_action, "value"))
            else (str(item_data.retention_action) if item_data.retention_action else RetentionAction.RETAIN.value)
        )
        cat_str = item_data.category.value if hasattr(item_data.category, "value") else str(item_data.category)

        item = MemoryItem(
            id=str(uuid.uuid4()),
            repository_id=repository_id,
            logical_key=item_data.logical_key,
            content=item_data.content.strip(),
            category=cat_str,
            retention_action=action_str,
            topic=item_data.topic,
            source_message_ids=item_data.source_message_ids,
            confidence=item_data.confidence,
            rationale=item_data.rationale,
            supersedes_item_id=supersedes_item_id,
            is_active=True
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def get_item(self, item_id: str) -> Optional[MemoryItem]:
        stmt = select(MemoryItem).where(MemoryItem.id == item_id)
        return self.db.scalars(stmt).first()

    def list_active_items(self, repository_id: Optional[str] = None) -> List[MemoryItem]:
        stmt = select(MemoryItem).where(MemoryItem.is_active == True)
        if repository_id:
            stmt = stmt.where(MemoryItem.repository_id == repository_id)
        return list(self.db.scalars(stmt).all())

    def deactivate_item(self, item_id: str) -> Optional[MemoryItem]:
        item = self.get_item(item_id)
        if item:
            item.is_active = False
            self.db.commit()
            self.db.refresh(item)
        return item

    def supersede_item(self, old_item_id: str, new_item_data: MemoryItemCreate, repository_id: Optional[str] = None) -> MemoryItem:
        old_item = self.deactivate_item(old_item_id)
        new_item = self.create_item(
            new_item_data,
            repository_id=repository_id or (old_item.repository_id if old_item else None),
            supersedes_item_id=old_item_id
        )
        return new_item

