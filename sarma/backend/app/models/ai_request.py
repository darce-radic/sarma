from sqlalchemy import Column, String, Float, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base
from app.models.base import TimestampMixin


class AIRequest(Base, TimestampMixin):
    """Model for tracking AI API requests for analytics and cost monitoring."""

    __tablename__ = "ai_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Request details
    provider = Column(String(50), nullable=False)  # 'gemini' or 'openai'
    feature = Column(String(100), nullable=False)  # 'meal_analysis', 'recipe_generation', 'chat'
    model = Column(String(100))  # Specific model used
    
    # Performance metrics
    response_time = Column(Float)  # Response time in seconds
    tokens_used = Column(Integer)  # Number of tokens consumed
    cost = Column(Float, default=0.0)  # Actual cost in USD
    
    # Request/Response data (optional, for debugging)
    prompt_text = Column(Text)  # Truncated prompt
    response_text = Column(Text)  # Truncated response
    
    # Status
    status = Column(String(50), default="success")  # 'success', 'error', 'timeout'
    error_message = Column(Text)  # If status is 'error'
    
    # Relationships
    user = relationship("User", back_populates="ai_requests")

    def __repr__(self):
        return f"<AIRequest(id={self.id}, user_id={self.user_id}, provider={self.provider}, feature={self.feature})>"
