"""
Meal Photo Analysis and Tracking Service
"""
from typing import List, Optional, Dict
from uuid import UUID
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func

from app.models.meal import (
    MealPhoto,
    MealPhotoIngredient,
    MealPhotoNutrition,
    MealLog,
    MealLogItem,
    ProcessingStatus
)
from app.schemas.meal import (
    MealPhotoCreate,
    MealLogCreate
)


class MealAnalysisService:
    """Service for AI-powered meal photo analysis"""
    
    @staticmethod
    async def analyze_meal_photo(
        db: Session,
        user_id: UUID,
        photo_data: MealPhotoCreate
    ) -> MealPhoto:
        """
        Analyze meal photo using GPT-4 Vision
        
        Process:
        1. Create meal photo record
        2. Send to GPT-4 Vision for analysis
        3. Detect ingredients and estimate quantities
        4. Calculate nutritional information
        5. Generate health score
        """
        
        # Create meal photo record
        meal_photo = MealPhoto(
            user_id=user_id,
            photo_url=str(photo_data.photo_url),
            meal_type=photo_data.meal_type,
            eaten_at=photo_data.eaten_at,
            location=photo_data.location,
            notes=photo_data.notes,
            processing_status=ProcessingStatus.PENDING
        )
        
        db.add(meal_photo)
        db.commit()
        db.refresh(meal_photo)
        
        # Queue for async processing
        # TODO: Send to Celery task for GPT-4 Vision analysis
        # await analyze_meal_photo_task.delay(meal_photo.id)
        
        return meal_photo
    
    @staticmethod
    async def process_meal_photo_with_gpt4_vision(
        db: Session,
        meal_photo_id: UUID
    ) -> MealPhoto:
        """
        Process meal photo with GPT-4 Vision
        
        TODO: Integrate with OpenAI GPT-4 Vision API
        """
        meal_photo = db.query(MealPhoto).filter(
            MealPhoto.id == meal_photo_id
        ).first()
        
        if not meal_photo:
            return None
        
        meal_photo.processing_status = ProcessingStatus.PROCESSING
        db.commit()
        
        try:
            # TODO: Call GPT-4 Vision API
            # response = await openai_client.chat.completions.create(
            #     model="gpt-4-vision-preview",
            #     messages=[{
            #         "role": "user",
            #         "content": [
            #             {"type": "text", "text": "Analyze this meal..."},
            #             {"type": "image_url", "image_url": meal_photo.photo_url}
            #         ]
            #     }]
            # )
            
            # Mock analysis result
            analysis_result = {
                "description": "Grilled chicken breast with mixed vegetables and quinoa",
                "confidence": 0.85,
                "ingredients": [
                    {
                        "name": "Chicken breast",
                        "quantity": 6,
                        "unit": "oz",
                        "confidence": 0.9,
                        "calories": 280,
                        "protein_g": 53,
                        "carbs_g": 0,
                        "fat_g": 6
                    },
                    {
                        "name": "Quinoa",
                        "quantity": 0.5,
                        "unit": "cup",
                        "confidence": 0.8,
                        "calories": 111,
                        "protein_g": 4,
                        "carbs_g": 20,
                        "fat_g": 2
                    },
                    {
                        "name": "Mixed vegetables",
                        "quantity": 1,
                        "unit": "cup",
                        "confidence": 0.85,
                        "calories": 50,
                        "protein_g": 2,
                        "carbs_g": 10,
                        "fat_g": 0
                    }
                ]
            }
            
            # Update meal photo with analysis
            meal_photo.ai_description = analysis_result["description"]
            meal_photo.ai_confidence = analysis_result["confidence"]
            meal_photo.detected_foods = [ing["name"] for ing in analysis_result["ingredients"]]
            
            # Add ingredients
            total_calories = 0
            total_protein = 0
            total_carbs = 0
            total_fat = 0
            
            for ing_data in analysis_result["ingredients"]:
                ingredient = MealPhotoIngredient(
                    meal_photo_id=meal_photo.id,
                    name=ing_data["name"],
                    quantity=ing_data["quantity"],
                    unit=ing_data["unit"],
                    confidence=ing_data["confidence"],
                    calories=ing_data["calories"],
                    protein_g=ing_data["protein_g"],
                    carbs_g=ing_data["carbs_g"],
                    fat_g=ing_data["fat_g"]
                )
                db.add(ingredient)
                
                total_calories += ing_data["calories"]
                total_protein += ing_data["protein_g"]
                total_carbs += ing_data["carbs_g"]
                total_fat += ing_data["fat_g"]
            
            # Update totals
            meal_photo.total_calories = total_calories
            meal_photo.total_protein_g = total_protein
            meal_photo.total_carbs_g = total_carbs
            meal_photo.total_fat_g = total_fat
            
            # Calculate health score
            meal_photo.health_score = await MealAnalysisService._calculate_health_score(
                total_calories, total_protein, total_carbs, total_fat
            )
            
            # Create detailed nutrition record
            nutrition = MealPhotoNutrition(
                meal_photo_id=meal_photo.id,
                calories=total_calories,
                protein_g=total_protein,
                carbohydrates_g=total_carbs,
                fat_g=total_fat,
                fiber_g=5,  # Estimated
                sugar_g=3,  # Estimated
                sodium_mg=400,  # Estimated
                health_score=meal_photo.health_score
            )
            db.add(nutrition)
            
            meal_photo.processing_status = ProcessingStatus.COMPLETED
            db.commit()
            db.refresh(meal_photo)
            
        except Exception as e:
            meal_photo.processing_status = ProcessingStatus.FAILED
            db.commit()
            raise e
        
        return meal_photo
    
    @staticmethod
    async def get_user_meal_photos(
        db: Session,
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50
    ) -> List[MealPhoto]:
        """Get user's meal photos with optional date range"""
        query = db.query(MealPhoto).filter(MealPhoto.user_id == user_id)
        
        if start_date:
            query = query.filter(MealPhoto.eaten_at >= start_date)
        if end_date:
            query = query.filter(MealPhoto.eaten_at <= end_date)
        
        return query.order_by(desc(MealPhoto.eaten_at)).limit(limit).all()
    
    @staticmethod
    async def confirm_meal_photo(
        db: Session,
        meal_photo_id: UUID,
        user_id: UUID,
        corrections: Optional[Dict] = None
    ) -> MealPhoto:
        """User confirms or corrects meal photo analysis"""
        meal_photo = db.query(MealPhoto).filter(
            MealPhoto.id == meal_photo_id,
            MealPhoto.user_id == user_id
        ).first()
        
        if not meal_photo:
            return None
        
        meal_photo.user_confirmed = True
        if corrections:
            meal_photo.user_corrections = corrections
        
        db.commit()
        db.refresh(meal_photo)
        
        return meal_photo
    
    @staticmethod
    async def create_meal_log(
        db: Session,
        user_id: UUID,
        log_data: MealLogCreate
    ) -> MealLog:
        """Create manual meal log entry"""
        
        # Calculate totals
        total_calories = sum(item.calories for item in log_data.items)
        total_protein = sum(item.protein_g for item in log_data.items)
        total_carbs = sum(item.carbs_g for item in log_data.items)
        total_fat = sum(item.fat_g for item in log_data.items)
        
        # Create meal log
        meal_log = MealLog(
            user_id=user_id,
            log_date=log_data.log_date,
            meal_type=log_data.meal_type,
            title=log_data.title,
            description=log_data.description,
            recipe_id=log_data.recipe_id,
            meal_photo_id=log_data.meal_photo_id,
            total_calories=total_calories,
            total_protein_g=total_protein,
            total_carbs_g=total_carbs,
            total_fat_g=total_fat,
            notes=log_data.notes,
            satisfaction_rating=log_data.satisfaction_rating
        )
        
        db.add(meal_log)
        db.flush()
        
        # Add meal items
        for item_data in log_data.items:
            item = MealLogItem(
                meal_log_id=meal_log.id,
                food_name=item_data.food_name,
                quantity=item_data.quantity,
                unit=item_data.unit,
                calories=item_data.calories,
                protein_g=item_data.protein_g,
                carbs_g=item_data.carbs_g,
                fat_g=item_data.fat_g
            )
            db.add(item)
        
        db.commit()
        db.refresh(meal_log)
        
        return meal_log
    
    @staticmethod
    async def get_daily_nutrition_summary(
        db: Session,
        user_id: UUID,
        target_date: date
    ) -> Dict:
        """Get nutritional summary for a specific day"""
        
        # Get all meal logs for the day
        start_datetime = datetime.combine(target_date, datetime.min.time())
        end_datetime = datetime.combine(target_date, datetime.max.time())
        
        meal_logs = db.query(MealLog).filter(
            MealLog.user_id == user_id,
            MealLog.log_date >= start_datetime,
            MealLog.log_date <= end_datetime
        ).all()
        
        # Calculate totals
        total_calories = sum(log.total_calories for log in meal_logs)
        total_protein = sum(log.total_protein_g for log in meal_logs)
        total_carbs = sum(log.total_carbs_g for log in meal_logs)
        total_fat = sum(log.total_fat_g for log in meal_logs)
        
        # Get meal photos for the day
        meal_photos = db.query(MealPhoto).filter(
            MealPhoto.user_id == user_id,
            MealPhoto.eaten_at >= start_datetime,
            MealPhoto.eaten_at <= end_datetime
        ).all()
        
        # Add photo nutrition
        for photo in meal_photos:
            if photo.total_calories:
                total_calories += photo.total_calories
                total_protein += photo.total_protein_g or 0
                total_carbs += photo.total_carbs_g or 0
                total_fat += photo.total_fat_g or 0
        
        return {
            "date": target_date,
            "total_calories": total_calories,
            "total_protein_g": total_protein,
            "total_carbs_g": total_carbs,
            "total_fat_g": total_fat,
            "meal_count": len(meal_logs) + len(meal_photos),
            "meals": meal_logs,
            "photos": meal_photos
        }
    
    @staticmethod
    async def get_nutrition_trends(
        db: Session,
        user_id: UUID,
        days: int = 7
    ) -> Dict:
        """Get nutrition trends over time"""
        
        from datetime import timedelta
        
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        daily_summaries = []
        current_date = start_date
        
        while current_date <= end_date:
            summary = await MealAnalysisService.get_daily_nutrition_summary(
                db, user_id, current_date
            )
            daily_summaries.append(summary)
            current_date += timedelta(days=1)
        
        # Calculate averages
        avg_calories = sum(s["total_calories"] for s in daily_summaries) / len(daily_summaries)
        avg_protein = sum(s["total_protein_g"] for s in daily_summaries) / len(daily_summaries)
        avg_carbs = sum(s["total_carbs_g"] for s in daily_summaries) / len(daily_summaries)
        avg_fat = sum(s["total_fat_g"] for s in daily_summaries) / len(daily_summaries)
        
        return {
            "period_days": days,
            "start_date": start_date,
            "end_date": end_date,
            "daily_summaries": daily_summaries,
            "averages": {
                "calories": avg_calories,
                "protein_g": avg_protein,
                "carbs_g": avg_carbs,
                "fat_g": avg_fat
            }
        }
    
    @staticmethod
    async def _calculate_health_score(
        calories: float,
        protein: float,
        carbs: float,
        fat: float
    ) -> float:
        """
        Calculate health score for a meal (0-100)
        
        Factors:
        - Macronutrient balance
        - Calorie appropriateness
        - Protein content
        - Fiber content (if available)
        """
        score = 50.0  # Base score
        
        # Protein score (higher protein = better)
        protein_pct = (protein * 4) / calories if calories > 0 else 0
        if protein_pct >= 0.3:
            score += 20
        elif protein_pct >= 0.2:
            score += 15
        elif protein_pct >= 0.15:
            score += 10
        
        # Calorie score (moderate calories = better)
        if 300 <= calories <= 600:
            score += 15
        elif 200 <= calories <= 800:
            score += 10
        elif calories < 200 or calories > 1000:
            score -= 10
        
        # Fat score (moderate fat = better)
        fat_pct = (fat * 9) / calories if calories > 0 else 0
        if 0.2 <= fat_pct <= 0.35:
            score += 15
        elif fat_pct > 0.5:
            score -= 10
        
        # Cap at 0-100
        return max(0, min(100, score))
