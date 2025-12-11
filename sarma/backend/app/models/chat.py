"""
AI Chat Assistant Models
"""
from datetime import datetime
from typing import Optional, List, Dict
from uuid import UUID, uuid4
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime,
    ForeignKey, Text, JSON, Index, CheckConstraint, Enum as SQLEnum
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
import enum

from app.core.database import Base


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class SessionStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class ChatSession(Base):
    """Chat sessions with AI assistant"""
    __tablename__ = "chat_sessions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="New Chat")
    status: Mapped[SessionStatus] = mapped_column(
        SQLEnum(SessionStatus),
        default=SessionStatus.ACTIVE,
        nullable=False
    )
    
    # Session metadata
    total_messages: Mapped[int] = mapped_column(Integer, default=0)
    last_message_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Context tracking
    context_data: Mapped[Optional[dict]] = mapped_column(JSONB)  # Current conversation context
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    user = relationship("User")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_session_user', 'user_id'),
        Index('idx_session_status', 'status'),
        Index('idx_session_updated', 'updated_at'),
    )


class ChatMessage(Base):
    """Individual messages in chat sessions"""
    __tablename__ = "chat_messages"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    role: Mapped[MessageRole] = mapped_column(SQLEnum(MessageRole), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Message metadata
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer)
    model_version: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Structured data
    intent: Mapped[Optional[str]] = mapped_column(String(100))  # recipe_search, health_question, etc.
    entities: Mapped[Optional[dict]] = mapped_column(JSONB)  # Extracted entities
    
    # Actions taken
    actions_executed: Mapped[Optional[List[dict]]] = mapped_column(JSONB)  # [{"type": "recipe_search", "result": {...}}]
    
    # Citations and sources
    sources: Mapped[Optional[List[dict]]] = mapped_column(JSONB)  # Referenced recipes, articles, etc.
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    feedback = relationship("ChatFeedback", back_populates="message", uselist=False, cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_message_session', 'session_id'),
        Index('idx_message_created', 'created_at'),
    )


class ChatFeedback(Base):
    """User feedback on AI responses"""
    __tablename__ = "chat_feedback"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    message_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("chat_messages.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Feedback type
    is_helpful: Mapped[bool] = mapped_column(Boolean, nullable=False)
    rating: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5
    
    # Detailed feedback
    feedback_text: Mapped[Optional[str]] = mapped_column(Text)
    feedback_categories: Mapped[Optional[List[str]]] = mapped_column(JSONB)  # ["inaccurate", "not_helpful", etc.]
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    message = relationship("ChatMessage", back_populates="feedback")
    user = relationship("User")
    
    __table_args__ = (
        Index('idx_feedback_message', 'message_id'),
        Index('idx_feedback_user', 'user_id'),
        CheckConstraint('rating >= 1 AND rating <= 5', name='check_feedback_rating'),
    )
