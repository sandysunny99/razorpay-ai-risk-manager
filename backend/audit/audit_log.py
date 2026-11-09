from abc import ABC, abstractmethod
import hashlib
import json
import threading
from typing import Any, Dict

from sqlalchemy import JSON, Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool


def canonical_hash(data: Dict[str, Any], prev_hash: str) -> str:
    serialized = json.dumps(data, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256((prev_hash + serialized).encode('utf-8')).hexdigest()

class AuditRepository(ABC):
    @abstractmethod
    def append_record(self, record: Dict[str, Any]) -> str:
        pass
    @abstractmethod
    def verify_chain(self) -> bool:
        pass

Base = declarative_base()

class AuditRecordModel(Base):
    __tablename__ = 'audit_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    audit_id = Column(String, unique=True, nullable=False)
    event_id = Column(String, nullable=False)
    merchant_id = Column(String, nullable=False)
    correlation_id = Column(String, nullable=False)
    timestamp = Column(Integer, nullable=False)
    record_type = Column(String, nullable=False)
    record_payload = Column(JSON, nullable=False)
    previous_hash = Column(String, nullable=False)
    current_hash = Column(String, nullable=False)

class SqlAuditRepository(AuditRepository):
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url, connect_args={"check_same_thread": False}, poolclass=StaticPool if ":memory:" in db_url else None)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self._append_lock = threading.Lock() # Fixes SQLite concurrency within process
        self._verify_lock = threading.Lock()
        self._verified_id = 0               # highest row id whose hash link has been verified
        self._verified_hash = "GENESIS"
        self._broken = False

    def append_record(self, record: Dict[str, Any]) -> str:
        with self._append_lock:
            with self.Session() as session:
                last_record = session.query(AuditRecordModel).order_by(AuditRecordModel.id.desc()).first()
                prev_hash = last_record.current_hash if last_record else "GENESIS"
                curr_hash = canonical_hash(record, prev_hash)

                new_entry = AuditRecordModel(
                    audit_id=record.get("audit_id", "unknown"),
                    event_id=record.get("event_id", "unknown"),
                    merchant_id=record.get("merchant_id", "unknown"),
                    correlation_id=record.get("correlation_id", "unknown"),
                    timestamp=record.get("timestamp", 0),
                    record_type=record.get("record_type", "decision"),
                    record_payload=record,
                    previous_hash=prev_hash,
                    current_hash=curr_hash
                )
                session.add(new_entry)
                session.commit()
                return curr_hash

    def verify_chain(self) -> bool:
        with self.Session() as session:
            records = session.query(AuditRecordModel).order_by(AuditRecordModel.id.asc()).all()
            expected_prev = "GENESIS"
            for r in records:
                if r.previous_hash != expected_prev:
                    return False
                recalculated = canonical_hash(r.record_payload, expected_prev)
                if recalculated != r.current_hash:
                    return False
                expected_prev = r.current_hash
            return True

    def verify_chain_incremental(self) -> bool:
        """Verify only rows appended since the last check (O(new rows) instead of O(ledger)).

        Rows already verified are not re-hashed, so out-of-band edits to old rows are caught by
        the full ``verify_chain()`` (exposed as GET /audit/verify), not by this hot-path check.
        Once a break is found the result stays False.
        """
        with self._verify_lock:
            if self._broken:
                return False
            with self.Session() as session:
                rows = (
                    session.query(AuditRecordModel)
                    .filter(AuditRecordModel.id > self._verified_id)
                    .order_by(AuditRecordModel.id.asc())
                    .all()
                )
                expected_prev = self._verified_hash
                for r in rows:
                    if r.previous_hash != expected_prev or canonical_hash(r.record_payload, expected_prev) != r.current_hash:
                        self._broken = True
                        return False
                    expected_prev = r.current_hash
                    self._verified_id = r.id
                self._verified_hash = expected_prev
            return True
