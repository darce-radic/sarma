"""
Chat Assistant API Endpoints
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.chat_service import ChatService

router = APIRouter()


class ChatMessageRequest(BaseModel):
    """Chat message request"""
    message: str
    context: Optional[dict] = None


class FeedbackRequest(BaseModel):
    """Feedback request"""
    is_helpful: bool
    rating: Optional[int] = None
    feedback_text: Optional[str] = None


@router.post("/sessions")
async def create_session(
    title: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create new chat session
    
    Each session maintains conversation context
    """
    session = await ChatService.create_chat_session(
        db,
        current_user.id,
        title
    )
    
    return session


@router.get("/sessions")
async def get_sessions(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's chat sessions"""
    sessions = await ChatService.get_chat_sessions(
        db,
        current_user.id,
        limit
    )
    return sessions


@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: UUID,
    request: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send message and get AI response
    
    AI assistant can:
    - Answer nutrition questions
    - Suggest recipes
    - Provide health advice
    - Help with meal planning
    - Interpret health data
    
    Uses GPT-4 Turbo with user context
    """
    message = await ChatService.send_message(
        db,
        current_user.id,
        session_id,
        request.message,
        request.context
    )
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return message


@router.get("/sessions/{session_id}/messages")
async def get_messages(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all messages in a session"""
    messages = await ChatService.get_chat_messages(
        db,
        current_user.id,
        session_id
    )
    
    return messages


@router.post("/messages/{message_id}/feedback")
async def submit_feedback(
    message_id: UUID,
    request: FeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit feedback on AI response
    
    Helps improve AI quality
    """
    feedback = await ChatService.submit_feedback(
        db,
        current_user.id,
        message_id,
        request.is_helpful,
        request.rating,
        request.feedback_text
    )
    
    return {
        "message": "Feedback submitted",
        "feedback_id": feedback.id
    }


@router.delete("/sessions/{session_id}")
async def archive_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Archive chat session"""
    success = await ChatService.archive_session(
        db,
        current_user.id,
        session_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return {"message": "Session archived"}
