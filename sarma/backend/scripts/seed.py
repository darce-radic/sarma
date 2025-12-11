"""
Seed script to populate demo data.

Usage:
  export DATABASE_URL=postgresql+asyncpg://...
  python -m scripts.seed
"""
import asyncio
from datetime import date, datetime, timedelta
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import AsyncSessionLocal, init_db
from app.core.security import get_password_hash
from app.models.user import User, UserHealthProfile, UserPreferences, SubscriptionTier, SubscriptionStatus
from app.models.shopping import ShoppingList, ShoppingListItem
from app.models.system_setting import SystemSetting


async def upsert_user(db: AsyncSession, email: str, password: str, is_admin: bool = False) -> User:
    existing = await db.execute(select(User).where(User.email == email))
    user = existing.scalar_one_or_none()
    if user:
        return user

    user = User(
        email=email,
        password_hash=get_password_hash(password),
        first_name="Admin" if is_admin else "Demo",
        last_name="User",
        subscription_tier=SubscriptionTier.PREMIUM if is_admin else SubscriptionTier.FREE,
        subscription_status=SubscriptionStatus.ACTIVE,
        onboarding_completed=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        email_verified=True,
        stripe_customer_id=None,
    )
    # Mark admin by email for current require_admin logic
    if is_admin:
        user.email = "admin@sarma.app"
    db.add(user)
    await db.flush()

    db.add(
        UserHealthProfile(
            user_id=user.id,
            height_cm=178,
            weight_kg=78,
            physical_activity_hours_week=3,
            sleep_hours_avg=7,
            stress_level=3,
            created_at=datetime.utcnow(),
        )
    )
    db.add(
        UserPreferences(
            user_id=user.id,
            dietary_restrictions=["low-carb"] if is_admin else [],
            cuisine_preferences=["mediterranean", "asian"],
            disliked_ingredients=["eggplant"],
            cooking_skill="intermediate",
            max_cooking_time_minutes=45,
            household_size=2,
            health_goals=["weight_loss"],
            target_daily_calories=2000,
            target_macros={"protein": 150, "carbs": 180, "fat": 60},
            created_at=datetime.utcnow(),
        )
    )
    return user


async def seed_shopping(db: AsyncSession, user: User) -> None:
    existing = await db.execute(select(ShoppingList).where(ShoppingList.user_id == user.id))
    if existing.scalar_one_or_none():
        return

    shopping_list = ShoppingList(
        user_id=user.id,
        title="Weekly Essentials",
        description="Auto-generated demo list",
        recipe_ids=[],
        week_start_date=datetime.utcnow().date(),
        week_end_date=(datetime.utcnow() + timedelta(days=7)).date(),
        estimated_total=65.50,
    )
    db.add(shopping_list)
    await db.flush()

    items = [
        ("Milk", 2, "L", "dairy", 3.20),
        ("Eggs", 12, "pcs", "dairy", 4.50),
        ("Chicken breast", 1, "kg", "meat", 12.90),
        ("Broccoli", 2, "bunch", "produce", 5.00),
        ("Olive oil", 1, "bottle", "pantry", 9.99),
    ]
    for name, qty, unit, category, price in items:
        db.add(
            ShoppingListItem(
                shopping_list_id=shopping_list.id,
                item_name=name,
                quantity=qty,
                unit=unit,
                category=category,
                estimated_price=price,
                created_at=datetime.utcnow(),
            )
        )


async def seed_settings(db: AsyncSession) -> None:
    defaults = {
        "COLES_WOOLWORTHS_MCP_URL": "http://localhost:3001",
        "OPENAI_API_KEY": "sk-demo",
        "GEMINI_API_KEY": "demo-gemini",
        "SPOONACULAR_API_KEY": "demo-spoonacular",
        "STRIPE_SECRET_KEY": "sk_test_demo",
    }
    existing = await db.execute(select(SystemSetting))
    present = {row.key for row in existing.scalars().all()}
    for key, value in defaults.items():
        if key not in present:
            db.add(SystemSetting(key=key, value=value))


async def main():
    # Ensure tables exist
    await init_db()
    async with AsyncSessionLocal() as db:
        admin = await upsert_user(db, "admin@sarma.app", "Admin123!", is_admin=True)
        user = await upsert_user(db, "user@example.com", "Password123!", is_admin=False)

        await seed_shopping(db, admin)
        await seed_shopping(db, user)
        await seed_settings(db)

        await db.commit()
    print("✅ Seed complete.")


if __name__ == "__main__":
    asyncio.run(main())

