import os
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.app.models.codebase_index import RepositoryIndexMeta, CodebaseFileRecord
from backend.app.services.codebase_indexer import compute_file_hash
from backend.app.core.logging import logger


class FreshnessManager:
    def __init__(self, db: Session, repository_root: Optional[str] = None):
        self.db = db
        self.repository_root = os.path.realpath(repository_root or os.getcwd())

    def check_file_freshness(self, repository_id: str, relative_path: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a file's indexed metadata matches the current live file on disk.
        Returns: (is_fresh: bool, reason: str)
        """
        abs_path = os.path.join(self.repository_root, relative_path)
        if not os.path.exists(abs_path):
            return False, "Live file was deleted from disk."

        # Fetch indexed record
        stmt = (
            select(CodebaseFileRecord)
            .join(RepositoryIndexMeta)
            .where(
                RepositoryIndexMeta.repository_id == repository_id,
                CodebaseFileRecord.relative_path == relative_path
            )
        )
        record = self.db.scalars(stmt).first()
        if not record:
            return False, "File is not present in codebase index."

        try:
            live_hash = compute_file_hash(abs_path)
            if live_hash != record.content_hash:
                record.is_stale = True
                self.db.commit()
                return False, f"Live file content hash differs from indexed hash (live: {live_hash[:8]}, index: {record.content_hash[:8]})."
            
            if record.is_stale:
                record.is_stale = False
                self.db.commit()
            return True, "Fresh: Live content hash matches index."
        except Exception as e:
            return False, f"Error computing live file hash: {str(e)}"

    def check_repository_freshness(self, repository_id: str) -> Dict[str, Any]:
        """Check all indexed files against the working directory."""
        stmt = (
            select(CodebaseFileRecord)
            .join(RepositoryIndexMeta)
            .where(RepositoryIndexMeta.repository_id == repository_id)
        )
        records = list(self.db.scalars(stmt).all())
        total = len(records)
        stale_files = []

        for rec in records:
            fresh, reason = self.check_file_freshness(repository_id, rec.relative_path)
            if not fresh:
                stale_files.append({"path": rec.relative_path, "reason": reason})

        return {
            "repository_id": repository_id,
            "total_indexed_files": total,
            "stale_count": len(stale_files),
            "stale_files": stale_files,
            "is_fresh": len(stale_files) == 0
        }
