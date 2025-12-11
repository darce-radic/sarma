"""
Referral and Viral Loop API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
import secrets
import string

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.referral import Referral, ReferralReward, SocialShare, ViralMilestone
from pydantic import BaseModel, EmailStr
from typing import List, Optional

router = APIRouter()


# Pydantic schemas
class ReferralCreate(BaseModel):
    referee_email: Optional[EmailStr] = None


class SocialShareCreate(BaseModel):
    platform: str
    share_type: str
    content_id: Optional[str] = None


class MilestoneShare(BaseModel):
    milestone_id: str
    platform: str


def generate_referral_code(length: int = 8) -> str:
    """Generate a unique referral code"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


@router.get("/my-code")
async def get_my_referral_code(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get or create user's referral code"""
    
    # Check if user already has a referral code
    result = await db.execute(
        select(Referral).where(Referral.referrer_id == current_user.id).limit(1)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        code = existing.code
    else:
        # Generate new unique code
        code = generate_referral_code()
        
        # Ensure uniqueness
        while True:
            check = await db.execute(select(Referral).where(Referral.code == code))
            if not check.scalar_one_or_none():
                break
            code = generate_referral_code()
        
        # Create referral record
        referral = Referral(
            referrer_id=current_user.id,
            code=code,
        )
        db.add(referral)
        await db.commit()
    
    # Count successful referrals
    referrals_count = await db.execute(
        select(func.count(Referral.id)).where(
            Referral.referrer_id == current_user.id,
            Referral.status == "completed"
        )
    )
    total_referrals = referrals_count.scalar() or 0
    
    # Calculate total rewards
    rewards_sum = await db.execute(
        select(func.sum(ReferralReward.reward_value)).where(
            ReferralReward.user_id == current_user.id,
            ReferralReward.is_claimed == True
        )
    )
    total_rewards = rewards_sum.scalar() or 0
    
    return {
        "code": code,
        "referral_url": f"https://sarma.app/signup?ref={code}",
        "total_referrals": total_referrals,
        "total_rewards": total_rewards,
        "reward_per_referral": 10.0,  # $10 credit per referral
        "share_message": f"Join me on Sarma Health! Use code {code} and get $10 off your first month! 🎉",
    }


@router.post("/send-invite")
async def send_referral_invite(
    invite: ReferralCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send referral invite to an email"""
    
    # Get user's referral code
    result = await db.execute(
        select(Referral).where(Referral.referrer_id == current_user.id).limit(1)
    )
    referral = result.scalar_one_or_none()
    
    if not referral:
        # Create one if doesn't exist
        code = generate_referral_code()
        referral = Referral(
            referrer_id=current_user.id,
            code=code,
        )
        db.add(referral)
        await db.commit()
        await db.refresh(referral)
    
    # Create pending referral for this email
    pending_referral = Referral(
        referrer_id=current_user.id,
        code=referral.code,
        referee_email=invite.referee_email,
        status="pending",
        source="email",
    )
    db.add(pending_referral)
    await db.commit()
    
    # TODO: Send email invitation
    # send_email(
    #     to=invite.referee_email,
    #     subject=f"{current_user.full_name} invited you to Sarma Health!",
    #     body=f"Join me on Sarma Health! Use code {referral.code}..."
    # )
    
    return {
        "message": "Invitation sent!",
        "referee_email": invite.referee_email,
        "code": referral.code,
    }


@router.get("/stats")
async def get_referral_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's referral statistics"""
    
    # Total referrals by status
    stats_query = select(
        Referral.status,
        func.count(Referral.id).label("count")
    ).where(
        Referral.referrer_id == current_user.id
    ).group_by(Referral.status)
    
    result = await db.execute(stats_query)
    status_counts = {row.status: row.count for row in result}
    
    # Recent referrals
    recent_query = select(Referral).where(
        Referral.referrer_id == current_user.id
    ).order_by(Referral.created_at.desc()).limit(10)
    
    recent_result = await db.execute(recent_query)
    recent_referrals = recent_result.scalars().all()
    
    # Total rewards earned
    rewards_query = select(
        func.sum(ReferralReward.reward_value).label("total"),
        func.count(ReferralReward.id).label("count")
    ).where(
        ReferralReward.user_id == current_user.id,
        ReferralReward.is_claimed == True
    )
    
    rewards_result = await db.execute(rewards_query)
    rewards_row = rewards_result.first()
    
    return {
        "total_pending": status_counts.get("pending", 0),
        "total_completed": status_counts.get("completed", 0),
        "total_rewarded": status_counts.get("rewarded", 0),
        "total_rewards_earned": rewards_row.total or 0,
        "total_rewards_count": rewards_row.count or 0,
        "recent_referrals": [
            {
                "id": str(ref.id),
                "email": ref.referee_email,
                "status": ref.status,
                "created_at": ref.created_at.isoformat() if ref.created_at else None,
            }
            for ref in recent_referrals
        ],
    }


@router.post("/share")
async def track_social_share(
    share: SocialShareCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Track when user shares content on social media"""
    
    social_share = SocialShare(
        user_id=current_user.id,
        platform=share.platform,
        share_type=share.share_type,
        content_id=share.content_id,
    )
    db.add(social_share)
    await db.commit()
    
    # Give user reward for sharing (e.g., 1 bonus AI request)
    # TODO: Implement reward logic
    
    return {
        "message": "Share tracked! Thanks for spreading the word! 🎉",
        "bonus_requests": 1,
    }


@router.get("/milestones")
async def get_user_milestones(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's shareable milestones"""
    
    result = await db.execute(
        select(ViralMilestone).where(
            ViralMilestone.user_id == current_user.id
        ).order_by(ViralMilestone.created_at.desc())
    )
    milestones = result.scalars().all()
    
    return {
        "milestones": [
            {
                "id": str(m.id),
                "type": m.milestone_type,
                "value": m.milestone_value,
                "title": m.title,
                "description": m.description,
                "is_shared": m.is_shared,
                "share_count": m.share_count,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in milestones
        ]
    }


@router.post("/milestone/share")
async def share_milestone(
    share: MilestoneShare,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Share a milestone on social media"""
    
    # Get milestone
    result = await db.execute(
        select(ViralMilestone).where(
            ViralMilestone.id == share.milestone_id,
            ViralMilestone.user_id == current_user.id
        )
    )
    milestone = result.scalar_one_or_none()
    
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
    
    # Update milestone
    milestone.is_shared = True
    milestone.shared_at = datetime.utcnow()
    milestone.share_count += 1
    
    # Track social share
    social_share = SocialShare(
        user_id=current_user.id,
        platform=share.platform,
        share_type="milestone",
        content_id=milestone.id,
    )
    db.add(social_share)
    
    await db.commit()
    
    return {
        "message": "Milestone shared! 🎉",
        "share_url": f"https://sarma.app/milestone/{milestone.id}",
    }


@router.get("/leaderboard")
async def get_referral_leaderboard(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get top referrers leaderboard"""
    
    # Get top referrers
    query = select(
        Referral.referrer_id,
        func.count(Referral.id).label("referral_count")
    ).where(
        Referral.status == "completed"
    ).group_by(
        Referral.referrer_id
    ).order_by(
        func.count(Referral.id).desc()
    ).limit(limit)
    
    result = await db.execute(query)
    top_referrers = result.all()
    
    # Get user details
    leaderboard = []
    for ref in top_referrers:
        user_result = await db.execute(
            select(User).where(User.id == ref.referrer_id)
        )
        user = user_result.scalar_one_or_none()
        
        if user:
            leaderboard.append({
                "user_id": str(user.id),
                "name": user.full_name or "Anonymous",
                "referral_count": ref.referral_count,
                "is_current_user": user.id == current_user.id,
            })
    
    # Find current user's rank
    user_rank_query = select(
        func.count(Referral.id).label("count")
    ).where(
        Referral.referrer_id == current_user.id,
        Referral.status == "completed"
    )
    
    user_rank_result = await db.execute(user_rank_query)
    user_referrals = user_rank_result.scalar() or 0
    
    return {
        "leaderboard": leaderboard,
        "your_rank": user_referrals,
        "message": "Top referrers this month!",
    }
