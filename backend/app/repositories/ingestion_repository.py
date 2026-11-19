"""Ingestion record repository — user-scoped tracking of ingestion jobs."""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.ingestion import IngestionRecord


class IngestionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: str, source: str, filename: Optional[str] = None) -> IngestionRecord:
        record = IngestionRecord(
            user_id=user_id,
            source=source,
            filename=filename,
            status="processing",
            imported_count=0,
            rejected_count=0,
            duplicates_skipped=0,
        )
        self.db.add(record)
        self.db.flush()
        return record

    def update(
        self,
        record: IngestionRecord,
        status: str,
        imported_count: int = 0,
        rejected_count: int = 0,
        duplicates_skipped: int = 0,
        error_message: Optional[str] = None,
    ) -> IngestionRecord:
        record.status = status
        record.imported_count = imported_count
        record.rejected_count = rejected_count
        record.duplicates_skipped = duplicates_skipped
        record.error_message = error_message
        self.db.flush()
        return record
