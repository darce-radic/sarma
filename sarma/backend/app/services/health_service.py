"""
Health Assessment Business Logic Service
"""
from typing import List, Dict, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.health import (
    HealthAssessment,
    HealthMetric,
    HealthGoal,
    HealthInsight
)
from app.models.user import User
from app.schemas.health import (
    HealthAssessmentCreate,
    HealthMetricCreate,
    HealthGoalCreate
)


class HealthAssessmentService:
    """Service for health assessment and risk analysis"""
    
    @staticmethod
    async def create_assessment(
        db: Session,
        user_id: UUID,
        assessment_data: HealthAssessmentCreate
    ) -> HealthAssessment:
        """
        Create comprehensive health assessment with AI-powered risk analysis
        """
        # Calculate BMI
        bmi = None
        if assessment_data.weight_lbs and assessment_data.height_inches:
            bmi = (assessment_data.weight_lbs * 703) / (assessment_data.height_inches ** 2)
        
        # Create assessment
        assessment = HealthAssessment(
            user_id=user_id,
            assessment_date=datetime.utcnow(),
            status="completed",
            current_conditions=assessment_data.current_conditions,
            medications=assessment_data.medications,
            allergies=assessment_data.allergies,
            family_history=assessment_data.family_history,
            weight_lbs=assessment_data.weight_lbs,
            height_inches=assessment_data.height_inches,
            bmi=bmi,
            hba1c=assessment_data.hba1c,
            fasting_glucose_mg_dl=assessment_data.fasting_glucose_mg_dl,
            total_cholesterol_mg_dl=assessment_data.total_cholesterol_mg_dl,
            ldl_cholesterol_mg_dl=assessment_data.ldl_cholesterol_mg_dl,
            hdl_cholesterol_mg_dl=assessment_data.hdl_cholesterol_mg_dl,
            triglycerides_mg_dl=assessment_data.triglycerides_mg_dl,
            blood_pressure_systolic=assessment_data.blood_pressure_systolic,
            blood_pressure_diastolic=assessment_data.blood_pressure_diastolic
        )
        
        # AI Risk Analysis (placeholder for GPT-4 integration)
        assessment.risk_scores = await HealthAssessmentService._calculate_risk_scores(
            assessment_data
        )
        
        # Generate personalized recommendations
        assessment.personalized_recommendations = await HealthAssessmentService._generate_recommendations(
            assessment_data,
            assessment.risk_scores
        )
        
        # Set dietary restrictions based on conditions
        assessment.dietary_restrictions = await HealthAssessmentService._determine_dietary_restrictions(
            assessment_data.current_conditions,
            assessment_data.allergies
        )
        
        # Calculate nutritional targets
        targets = await HealthAssessmentService._calculate_nutrition_targets(
            assessment_data,
            bmi
        )
        assessment.target_calories_daily = targets["calories"]
        assessment.target_protein_g = targets["protein"]
        assessment.target_carbs_g = targets["carbs"]
        assessment.target_fat_g = targets["fat"]
        assessment.target_sodium_mg = targets["sodium"]
        assessment.target_sugar_g = targets["sugar"]
        
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
        
        return assessment
    
    @staticmethod
    async def _calculate_risk_scores(data: HealthAssessmentCreate) -> Dict:
        """
        Calculate disease risk scores using medical algorithms
        
        TODO: Integrate with OpenAI GPT-4 for advanced risk analysis
        """
        risk_scores = {}
        
        # Diabetes risk
        if data.hba1c:
            if data.hba1c >= 6.5:
                risk_scores["diabetes"] = "high"
            elif data.hba1c >= 5.7:
                risk_scores["diabetes"] = "medium"
            else:
                risk_scores["diabetes"] = "low"
        
        # Cardiovascular risk (simplified Framingham)
        cv_risk = 0
        if data.blood_pressure_systolic and data.blood_pressure_systolic >= 140:
            cv_risk += 2
        if data.total_cholesterol_mg_dl and data.total_cholesterol_mg_dl >= 240:
            cv_risk += 2
        if "diabetes" in (data.current_conditions or []):
            cv_risk += 3
        
        if cv_risk >= 5:
            risk_scores["cardiovascular"] = "high"
        elif cv_risk >= 3:
            risk_scores["cardiovascular"] = "medium"
        else:
            risk_scores["cardiovascular"] = "low"
        
        return risk_scores
    
    @staticmethod
    async def _generate_recommendations(
        data: HealthAssessmentCreate,
        risk_scores: Dict
    ) -> List[Dict]:
        """
        Generate personalized health recommendations
        
        TODO: Use OpenAI GPT-4 for personalized recommendations
        """
        recommendations = []
        
        # Diabetes recommendations
        if risk_scores.get("diabetes") in ["high", "medium"]:
            recommendations.append({
                "category": "nutrition",
                "priority": "high",
                "title": "Focus on Low Glycemic Foods",
                "description": "Choose foods with low glycemic index to manage blood sugar",
                "action_items": [
                    "Replace white rice with quinoa or brown rice",
                    "Choose whole grain bread over white bread",
                    "Add more non-starchy vegetables to meals"
                ]
            })
        
        # Cardiovascular recommendations
        if risk_scores.get("cardiovascular") in ["high", "medium"]:
            recommendations.append({
                "category": "nutrition",
                "priority": "high",
                "title": "Heart-Healthy Diet",
                "description": "Adopt Mediterranean-style eating patterns",
                "action_items": [
                    "Increase omega-3 rich fish (salmon, mackerel)",
                    "Use olive oil as primary cooking fat",
                    "Reduce sodium intake to <2300mg daily",
                    "Limit saturated fat to <10% of calories"
                ]
            })
        
        return recommendations
    
    @staticmethod
    async def _determine_dietary_restrictions(
        conditions: Optional[List[str]],
        allergies: Optional[List[str]]
    ) -> List[str]:
        """Determine dietary restrictions based on health conditions"""
        restrictions = []
        
        if conditions:
            conditions_lower = [c.lower() for c in conditions]
            
            if any("diabetes" in c for c in conditions_lower):
                restrictions.extend(["low_sugar", "low_glycemic"])
            
            if any("hypertension" in c or "blood pressure" in c for c in conditions_lower):
                restrictions.append("low_sodium")
            
            if any("kidney" in c for c in conditions_lower):
                restrictions.extend(["low_sodium", "low_potassium"])
            
            if any("celiac" in c for c in conditions_lower):
                restrictions.append("gluten_free")
        
        if allergies:
            for allergy in allergies:
                restrictions.append(f"no_{allergy.lower()}")
        
        return list(set(restrictions))
    
    @staticmethod
    async def _calculate_nutrition_targets(
        data: HealthAssessmentCreate,
        bmi: Optional[float]
    ) -> Dict:
        """
        Calculate personalized nutrition targets
        
        Based on:
        - Current weight and BMI
        - Health conditions
        - Activity level (default: moderate)
        """
        # Base calorie calculation (Harris-Benedict equation simplified)
        # TODO: Get gender and age from user profile
        base_calories = 2000  # Default
        
        if data.weight_lbs:
            # Simplified calculation: 12-15 cal/lb depending on goals
            base_calories = int(data.weight_lbs * 13)
        
        # Adjust for health conditions
        if data.current_conditions:
            if any("diabetes" in c.lower() for c in data.current_conditions):
                # Moderate calorie restriction for diabetes
                base_calories = int(base_calories * 0.9)
        
        # Macronutrient distribution
        # Default: 30% protein, 40% carbs, 30% fat
        protein_pct = 0.30
        carbs_pct = 0.40
        fat_pct = 0.30
        
        # Adjust for diabetes (lower carbs)
        if data.current_conditions and any("diabetes" in c.lower() for c in data.current_conditions):
            protein_pct = 0.30
            carbs_pct = 0.35
            fat_pct = 0.35
        
        return {
            "calories": base_calories,
            "protein": int((base_calories * protein_pct) / 4),  # 4 cal/g
            "carbs": int((base_calories * carbs_pct) / 4),
            "fat": int((base_calories * fat_pct) / 9),  # 9 cal/g
            "sodium": 2300,  # mg (AHA recommendation)
            "sugar": 50  # g (AHA recommendation: < 10% of calories)
        }
    
    @staticmethod
    async def get_latest_assessment(
        db: Session,
        user_id: UUID
    ) -> Optional[HealthAssessment]:
        """Get user's most recent health assessment"""
        return db.query(HealthAssessment).filter(
            HealthAssessment.user_id == user_id
        ).order_by(desc(HealthAssessment.assessment_date)).first()
    
    @staticmethod
    async def add_health_metric(
        db: Session,
        user_id: UUID,
        metric_data: HealthMetricCreate
    ) -> HealthMetric:
        """Add a new health metric reading"""
        metric = HealthMetric(
            user_id=user_id,
            recorded_at=metric_data.recorded_at or datetime.utcnow(),
            metric_type=metric_data.metric_type,
            value=metric_data.value,
            value_secondary=metric_data.value_secondary,
            unit=metric_data.unit,
            notes=metric_data.notes,
            source="manual"
        )
        
        db.add(metric)
        db.commit()
        db.refresh(metric)
        
        return metric
