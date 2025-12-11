"""
Brand Partnership and B2B Models
"""
from datetime import datetime, date
from typing import Optional, List
from uuid import UUID, uuid4
from decimal import Decimal
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Date, Numeric,
    ForeignKey, Text, JSON, Index, CheckConstraint, Enum as SQLEnum
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
import enum

from app.core.database import Base


class PartnershipTier(str, enum.Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


class PartnershipStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    EXPIRED = "expired"


class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class Brand(Base):
    """Brand partners"""
    __tablename__ = "brands"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Company details
    company_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    legal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    website: Mapped[Optional[str]] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Branding
    logo_url: Mapped[Optional[str]] = mapped_column(String(500))
    brand_colors: Mapped[Optional[dict]] = mapped_column(JSONB)  # {"primary": "#FF0000", "secondary": "#00FF00"}
    
    # Contact
    primary_contact_name: Mapped[str] = mapped_column(String(255), nullable=False)
    primary_contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    primary_contact_phone: Mapped[Optional[str]] = mapped_column(String(20))
    
    # Business info
    industry: Mapped[str] = mapped_column(String(100), nullable=False)
    company_size: Mapped[Optional[str]] = mapped_column(String(50))  # 1-50, 51-200, etc.
    annual_revenue: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    partnerships = relationship("BrandPartnership", back_populates="brand", cascade="all, delete-orphan")
    products = relationship("BrandProduct", back_populates="brand", cascade="all, delete-orphan")
    campaigns = relationship("BrandCampaign", back_populates="brand", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_brand_name', 'company_name'),
        Index('idx_brand_active', 'is_active'),
    )


class BrandPartnership(Base):
    """Partnership agreements with brands"""
    __tablename__ = "brand_partnerships"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    brand_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Partnership details
    partnership_name: Mapped[str] = mapped_column(String(255), nullable=False)
    tier: Mapped[PartnershipTier] = mapped_column(SQLEnum(PartnershipTier), nullable=False)
    status: Mapped[PartnershipStatus] = mapped_column(
        SQLEnum(PartnershipStatus),
        default=PartnershipStatus.PENDING,
        nullable=False
    )
    
    # Contract dates
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Financial terms
    monthly_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    commission_rate: Mapped[Optional[float]] = mapped_column(Float)  # 0-1 (e.g., 0.05 = 5%)
    revenue_share_rate: Mapped[Optional[float]] = mapped_column(Float)  # 0-1
    
    # Contract details
    contract_url: Mapped[Optional[str]] = mapped_column(String(500))
    terms: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    # Benefits and features
    featured_placement: Mapped[bool] = mapped_column(Boolean, default=False)
    custom_landing_page: Mapped[bool] = mapped_column(Boolean, default=False)
    dedicated_support: Mapped[bool] = mapped_column(Boolean, default=False)
    api_access: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Performance targets
    monthly_impression_target: Mapped[Optional[int]] = mapped_column(Integer)
    monthly_conversion_target: Mapped[Optional[int]] = mapped_column(Integer)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    brand = relationship("Brand", back_populates="partnerships")
    
    __table_args__ = (
        Index('idx_partnership_brand', 'brand_id'),
        Index('idx_partnership_status', 'status'),
        Index('idx_partnership_dates', 'start_date', 'end_date'),
        CheckConstraint('monthly_fee >= 0', name='check_monthly_fee'),
        CheckConstraint('commission_rate >= 0 AND commission_rate <= 1', name='check_commission_rate'),
    )


class BrandProduct(Base):
    """Products offered by brand partners"""
    __tablename__ = "brand_products"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    brand_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Product info
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Images
    image_url: Mapped[Optional[str]] = mapped_column(String(500))
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Pricing
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    discount_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    
    # Links
    purchase_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Attributes
    is_organic: Mapped[bool] = mapped_column(Boolean, default=False)
    is_gluten_free: Mapped[bool] = mapped_column(Boolean, default=False)
    is_vegan: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Nutritional data
    nutrition_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    brand = relationship("Brand", back_populates="products")
    
    __table_args__ = (
        Index('idx_brand_product_brand', 'brand_id'),
        Index('idx_brand_product_category', 'category'),
        Index('idx_brand_product_active', 'is_active'),
        CheckConstraint('price >= 0', name='check_product_price'),
    )


class BrandCampaign(Base):
    """Marketing campaigns from brand partners"""
    __tablename__ = "brand_campaigns"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    brand_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Campaign details
    campaign_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    status: Mapped[CampaignStatus] = mapped_column(
        SQLEnum(CampaignStatus),
        default=CampaignStatus.DRAFT,
        nullable=False
    )
    
    # Dates
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Budget
    total_budget: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    spent_budget: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    
    # Creative assets
    banner_image_url: Mapped[Optional[str]] = mapped_column(String(500))
    video_url: Mapped[Optional[str]] = mapped_column(String(500))
    landing_page_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Targeting
    target_audience: Mapped[Optional[dict]] = mapped_column(JSONB)  # Demographics, interests, etc.
    target_health_conditions: Mapped[Optional[List[str]]] = mapped_column(JSONB)
    
    # Goals
    impression_goal: Mapped[Optional[int]] = mapped_column(Integer)
    click_goal: Mapped[Optional[int]] = mapped_column(Integer)
    conversion_goal: Mapped[Optional[int]] = mapped_column(Integer)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    brand = relationship("Brand", back_populates="campaigns")
    
    __table_args__ = (
        Index('idx_campaign_brand', 'brand_id'),
        Index('idx_campaign_status', 'status'),
        Index('idx_campaign_dates', 'start_date', 'end_date'),
        CheckConstraint('total_budget >= 0', name='check_campaign_budget'),
    )


class BrandAnalytics(Base):
    """Analytics for brand partnerships"""
    __tablename__ = "brand_analytics"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    brand_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    analytics_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    
    # Impressions and engagement
    total_impressions: Mapped[int] = mapped_column(Integer, default=0)
    total_clicks: Mapped[int] = mapped_column(Integer, default=0)
    total_conversions: Mapped[int] = mapped_column(Integer, default=0)
    
    # Revenue
    total_revenue: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    commission_earned: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    
    # User engagement
    unique_users_reached: Mapped[int] = mapped_column(Integer, default=0)
    recipes_featuring_products: Mapped[int] = mapped_column(Integer, default=0)
    
    # Performance metrics
    click_through_rate: Mapped[Optional[float]] = mapped_column(Float)
    conversion_rate: Mapped[Optional[float]] = mapped_column(Float)
    
    # Detailed breakdown
    metrics_by_product: Mapped[Optional[dict]] = mapped_column(JSONB)
    metrics_by_campaign: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    brand = relationship("Brand")
    
    __table_args__ = (
        Index('idx_analytics_brand_date', 'brand_id', 'analytics_date', unique=True),
    )
