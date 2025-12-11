"""
AI Chat Assistant Service
"""
from typing import List, Optional, Dict
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.chat import (
    ChatSession,
    ChatMessage,
    ChatFeedback,
    MessageRole,
    SessionStatus
)


class ChatService:
    """Service for AI-powered chat assistant"""
    
    @staticmethod
    async def create_chat_session(
        db: Session,
        user_id: UUID,
        title: Optional[str] = None
    ) -> ChatSession:
        """Create a new chat session"""
        
        session = ChatSession(
            user_id=user_id,
            title=title or "New Chat",
            status=SessionStatus.ACTIVE,
            total_messages=0
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        return session
    
    @staticmethod
    async def send_message(
        db: Session,
        user_id: UUID,
        session_id: UUID,
        message_content: str,
        context: Optional[Dict] = None
    ) -> ChatMessage:
        """
        Send message and get AI response
        
        Uses GPT-4 Turbo with:
        - User health context
        - Conversation history
        - Recipe knowledge base (RAG)
        """
        
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id
        ).first()
        
        if not session:
            return None
        
        # Create user message
        user_message = ChatMessage(
            session_id=session_id,
            role=MessageRole.USER,
            content=message_content
        )
        
        db.add(user_message)
        db.flush()
        
        # Get conversation history
        history = await ChatService._get_conversation_history(db, session_id)
        
        # Get user context
        user_context = await ChatService._get_user_context(db, user_id)
        
        # Generate AI response
        ai_response = await ChatService._generate_ai_response(
            message_content,
            history,
            user_context,
            context
        )
        
        # Create assistant message
        assistant_message = ChatMessage(
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=ai_response["content"],
            tokens_used=ai_response.get("tokens_used"),
            model_version=ai_response.get("model"),
            intent=ai_response.get("intent"),
            entities=ai_response.get("entities"),
            actions_executed=ai_response.get("actions"),
            sources=ai_response.get("sources")
        )
        
        db.add(assistant_message)
        
        # Update session
        session.total_messages += 2
        session.last_message_at = datetime.utcnow()
        
        # Update title from first message
        if session.total_messages == 2:
            session.title = message_content[:50]
        
        db.commit()
        db.refresh(assistant_message)
        
        return assistant_message
    
    @staticmethod
    async def get_chat_sessions(
        db: Session,
        user_id: UUID,
        limit: int = 50
    ) -> List[ChatSession]:
        """Get user's chat sessions"""
        return db.query(ChatSession).filter(
            ChatSession.user_id == user_id,
            ChatSession.status == SessionStatus.ACTIVE
        ).order_by(desc(ChatSession.updated_at)).limit(limit).all()
    
    @staticmethod
    async def get_chat_messages(
        db: Session,
        user_id: UUID,
        session_id: UUID
    ) -> List[ChatMessage]:
        """Get messages in a chat session"""
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id
        ).first()
        
        if not session:
            return []
        
        return db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at).all()
    
    @staticmethod
    async def submit_feedback(
        db: Session,
        user_id: UUID,
        message_id: UUID,
        is_helpful: bool,
        rating: Optional[int] = None,
        feedback_text: Optional[str] = None
    ) -> ChatFeedback:
        """Submit feedback on AI response"""
        
        feedback = ChatFeedback(
            message_id=message_id,
            user_id=user_id,
            is_helpful=is_helpful,
            rating=rating,
            feedback_text=feedback_text
        )
        
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        
        return feedback
    
    @staticmethod
    async def archive_session(
        db: Session,
        user_id: UUID,
        session_id: UUID
    ) -> bool:
        """Archive a chat session"""
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id
        ).first()
        
        if not session:
            return False
        
        session.status = SessionStatus.ARCHIVED
        db.commit()
        
        return True
    
    @staticmethod
    async def _get_conversation_history(
        db: Session,
        session_id: UUID,
        limit: int = 10
    ) -> List[Dict]:
        """Get recent conversation history"""
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(desc(ChatMessage.created_at)).limit(limit).all()
        
        return [
            {
                "role": msg.role,
                "content": msg.content
            }
            for msg in reversed(messages)
        ]
    
    @staticmethod
    async def _get_user_context(db: Session, user_id: UUID) -> Dict:
        """
        Get user context for personalized responses
        
        Includes:
        - Health conditions
        - Dietary preferences
        - Nutrition goals
        - Recent meals
        """
        from app.models.health import HealthAssessment
        from app.models.user import User
        
        user = db.query(User).filter(User.id == user_id).first()
        
        # Get latest health assessment
        assessment = db.query(HealthAssessment).filter(
            HealthAssessment.user_id == user_id
        ).order_by(desc(HealthAssessment.assessment_date)).first()
        
        context = {
            "user_name": f"{user.first_name} {user.last_name}",
            "health_conditions": [],
            "dietary_restrictions": [],
            "nutrition_goals": {}
        }
        
        if assessment:
            context["health_conditions"] = assessment.current_conditions or []
            context["dietary_restrictions"] = assessment.dietary_restrictions or []
            context["nutrition_goals"] = {
                "calories": assessment.target_calories_daily,
                "protein": assessment.target_protein_g,
                "carbs": assessment.target_carbs_g,
                "fat": assessment.target_fat_g
            }
        
        return context
    
    @staticmethod
    async def _generate_ai_response(
        user_message: str,
        history: List[Dict],
        user_context: Dict,
        additional_context: Optional[Dict] = None
    ) -> Dict:
        """
        Generate AI response using GPT-4 Turbo
        
        TODO: Integrate with OpenAI API
        """
        
        # Build system prompt with user context
        system_prompt = f"""You are Forecast, an AI health and nutrition assistant.

User Profile:
- Name: {user_context.get('user_name')}
- Health Conditions: {', '.join(user_context.get('health_conditions', []))}
- Dietary Restrictions: {', '.join(user_context.get('dietary_restrictions', []))}
- Nutrition Goals: {user_context.get('nutrition_goals')}

You help users:
1. Find healthy recipes matching their needs
2. Understand nutrition and health
3. Plan meals and shopping
4. Track their health progress
5. Make better food choices

Be empathetic, encouraging, and evidence-based."""
        
        # TODO: Call OpenAI GPT-4 API
        # response = await openai_client.chat.completions.create(
        #     model="gpt-4-turbo-preview",
        #     messages=[
        #         {"role": "system", "content": system_prompt},
        #         *history,
        #         {"role": "user", "content": user_message}
        #     ],
        #     temperature=0.7,
        #     max_tokens=500
        # )
        
        # Mock response for now
        mock_response = f"""I understand you're asking about: {user_message}

Based on your health profile (conditions: {', '.join(user_context.get('health_conditions', ['none']))}), 
I'd recommend focusing on balanced nutrition with plenty of vegetables, lean proteins, and whole grains.

Would you like me to:
1. Suggest some specific recipes?
2. Explain nutritional concepts?
3. Help plan your meals?

Let me know how I can help!"""
        
        return {
            "content": mock_response,
            "tokens_used": 150,
            "model": "gpt-4-turbo-preview",
            "intent": "general_query",
            "entities": {},
            "actions": [],
            "sources": []
        }
