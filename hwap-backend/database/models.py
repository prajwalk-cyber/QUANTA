"""SQLAlchemy models for QUANTA backend."""
from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, DateTime, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[str] = mapped_column(String(255), default="default-client")
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    organization: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class PublicKey(Base):
    __tablename__ = "public_keys"
    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[str] = mapped_column(String(255), default="default-client")
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    algorithm: Mapped[str] = mapped_column(String(50))
    public_key_hex: Mapped[str] = mapped_column(Text)
    byte_size: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Session(Base):
    __tablename__ = "sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[str] = mapped_column(String(255), default="default-client")
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    tier: Mapped[int] = mapped_column(Integer)
    k_hybrid_hash: Mapped[str] = mapped_column(String(255))
    shst_token: Mapped[str] = mapped_column(String(512))
    expires_at: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Signature(Base):
    __tablename__ = "signatures"
    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[str] = mapped_column(String(255), default="default-client")
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    message: Mapped[str] = mapped_column(Text)
    signature_hex: Mapped[str] = mapped_column(Text)
    sig_size_bytes: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[str] = mapped_column(String(255), default="default-client")
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user: Mapped[str] = mapped_column(String(255))
    operation: Mapped[str] = mapped_column(String(255))
    algorithm: Mapped[str] = mapped_column(String(50))
    result: Mapped[str] = mapped_column(String(255))
