import os, datetime as dt
from sqlalchemy import create_engine, String, Integer, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL", "sqlite:///./bayora.db"), pool_pre_ping=True)
SessionLocal = sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase): pass

class EvalSession(Base):
    __tablename__ = "sessions"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    status: Mapped[str] = mapped_column(String(16), default="active")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    red_quota_used: Mapped[int] = mapped_column(Integer, default=0)

class AuditEvent(Base):
    __tablename__ = "events"
    __table_args__ = (UniqueConstraint("session_id", "idx"),)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"), index=True)
    idx: Mapped[int] = mapped_column(Integer)
    ts: Mapped[str] = mapped_column(String(40))
    subject: Mapped[str] = mapped_column(String(16))
    action: Mapped[str] = mapped_column(String(32))
    resource: Mapped[str] = mapped_column(String(48))
    decision: Mapped[str] = mapped_column(String(8))
    note: Mapped[str] = mapped_column(Text, default="")
    prev_hash: Mapped[str] = mapped_column(String(64))
    hash: Mapped[str] = mapped_column(String(64))

def init_db(): Base.metadata.create_all(engine)
