"""
Shopping and Multi-Store Integration Models
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
from decimal import Decimal
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Numeric,
    ForeignKey, Text, JSON, Index, CheckConstraint, Enum as SQLEnum
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
import enum

from app.core.database import Base


class OrderStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class StoreType(str, enum.Enum):
    INSTACART = "instacart"
    AMAZON_FRESH = "amazon_fresh"
    WALMART = "walmart"
    KROGER = "kroger"
    TARGET = "target"
    WHOLE_FOODS = "whole_foods"
    OTHER = "other"


class ShoppingList(Base):
    """Shopping lists generated from meal plans"""
    __tablename__ = "shopping_lists"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Source recipes
    recipe_ids: Mapped[List[UUID]] = mapped_column(JSONB, default=list)
    
    # Week planning
    week_start_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    week_end_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Budget
    estimated_total: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_purchased: Mapped[bool] = mapped_column(Boolean, default=False)
    purchased_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    user = relationship("User")
    items = relationship("ShoppingListItem", back_populates="shopping_list", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_shopping_list_user', 'user_id'),
        Index('idx_shopping_list_active', 'is_active'),
    )


class ShoppingListItem(Base):
    """Individual items in shopping lists"""
    __tablename__ = "shopping_list_items"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    shopping_list_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("shopping_lists.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Category for organization
    category: Mapped[str] = mapped_column(String(100), default="other")  # produce, dairy, meat, etc.
    
    # Product matching
    matched_product_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    product_name: Mapped[Optional[str]] = mapped_column(String(255))
    product_brand: Mapped[Optional[str]] = mapped_column(String(255))
    estimated_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    
    # User interaction
    is_checked: Mapped[bool] = mapped_column(Boolean, default=False)
    is_substituted: Mapped[bool] = mapped_column(Boolean, default=False)
    substitution_reason: Mapped[Optional[str]] = mapped_column(Text)
    
    # Source tracking
    recipe_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("recipes.id", ondelete="SET NULL")
    )
    
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    shopping_list = relationship("ShoppingList", back_populates="items")
    recipe = relationship("Recipe")
    
    __table_args__ = (
        Index('idx_list_item_list', 'shopping_list_id'),
        Index('idx_list_item_category', 'category'),
        CheckConstraint('quantity > 0', name='check_item_quantity'),
    )


class ShoppingOrder(Base):
    """Orders placed through integrated stores"""
    __tablename__ = "shopping_orders"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    shopping_list_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("shopping_lists.id", ondelete="SET NULL"),
        index=True
    )
    store_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("stores.id", ondelete="SET NULL"),
        index=True
    )
    
    # Order details
    order_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    external_order_id: Mapped[Optional[str]] = mapped_column(String(255))  # ID from Instacart, etc.
    
    # Financial
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    tax: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    delivery_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    tip: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    # Status tracking
    status: Mapped[OrderStatus] = mapped_column(SQLEnum(OrderStatus), default=OrderStatus.DRAFT, nullable=False)
    
    # Delivery
    delivery_address: Mapped[Optional[dict]] = mapped_column(JSONB)
    delivery_instructions: Mapped[Optional[str]] = mapped_column(Text)
    estimated_delivery_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Human-in-the-loop review
    requires_review: Mapped[bool] = mapped_column(Boolean, default=False)
    reviewed_by_user: Mapped[bool] = mapped_column(Boolean, default=False)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    user_modifications: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    user = relationship("User")
    shopping_list = relationship("ShoppingList")
    store = relationship("Store")
    items = relationship("ShoppingOrderItem", back_populates="order", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_order_user', 'user_id'),
        Index('idx_order_status', 'status'),
        Index('idx_order_date', 'created_at'),
        CheckConstraint('total >= 0', name='check_order_total'),
    )


class ShoppingOrderItem(Base):
    """Items in a shopping order"""
    __tablename__ = "shopping_order_items"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    order_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("shopping_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    product_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("store_products.id", ondelete="SET NULL")
    )
    
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    product_brand: Mapped[Optional[str]] = mapped_column(String(255))
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    # Substitutions
    was_substituted: Mapped[bool] = mapped_column(Boolean, default=False)
    original_product_name: Mapped[Optional[str]] = mapped_column(String(255))
    substitution_reason: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    order = relationship("ShoppingOrder", back_populates="items")
    product = relationship("StoreProduct")
    
    __table_args__ = (
        Index('idx_order_item_order', 'order_id'),
        CheckConstraint('quantity > 0', name='check_order_item_quantity'),
        CheckConstraint('unit_price >= 0', name='check_unit_price'),
    )


class Store(Base):
    """Integrated grocery stores"""
    __tablename__ = "stores"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    store_type: Mapped[StoreType] = mapped_column(SQLEnum(StoreType), nullable=False, index=True)
    store_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Location
    address: Mapped[Optional[str]] = mapped_column(String(500))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    state: Mapped[Optional[str]] = mapped_column(String(2))
    zip_code: Mapped[Optional[str]] = mapped_column(String(10))
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)
    
    # API integration
    external_store_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    api_endpoint: Mapped[Optional[str]] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Store metadata
    logo_url: Mapped[Optional[str]] = mapped_column(String(500))
    supports_delivery: Mapped[bool] = mapped_column(Boolean, default=True)
    supports_pickup: Mapped[bool] = mapped_column(Boolean, default=False)
    minimum_order: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    delivery_fee: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    __table_args__ = (
        Index('idx_store_type', 'store_type'),
        Index('idx_store_location', 'zip_code'),
    )


class StoreProduct(Base):
    """Products available at stores"""
    __tablename__ = "store_products"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    store_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("stores.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Product details
    product_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    brand: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # Identifiers
    upc: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    external_product_id: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Pricing
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)  # lb, oz, each, etc.
    unit_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))  # price per unit (e.g., per oz)
    
    # Images
    image_url: Mapped[Optional[str]] = mapped_column(String(500))
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Availability
    in_stock: Mapped[bool] = mapped_column(Boolean, default=True)
    is_organic: Mapped[bool] = mapped_column(Boolean, default=False)
    is_gluten_free: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Nutritional info (if available)
    nutrition_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    # Metadata
    last_price_update: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    store = relationship("Store")
    
    __table_args__ = (
        Index('idx_product_store_name', 'store_id', 'product_name'),
        Index('idx_product_category', 'category'),
        Index('idx_product_upc', 'upc'),
        CheckConstraint('price >= 0', name='check_product_price'),
    )
