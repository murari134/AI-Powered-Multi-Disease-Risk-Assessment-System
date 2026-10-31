"""
MediRisk 2.0 — Prediction & Assessment Coordinator Service
Phase 8 & 9: Complete Multi-Disease Assessment & Analytics

Connects ML inference engine with database persistence:
- Complete Health Assessment (all 10 diseases simultaneously)
- Individual Disease Assessment (single targeted disease)
- Saves HealthAssessment (input_data JSONB, assessment_mode)
- Saves DiseasePrediction (probabilities, risk level, model metadata)
- Saves PredictionAttributions (explainability factors)
- Saves Recommendations (clinical prototype guidance)
- Manages user prediction history and analytics queries
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.models.models import (
    AuditLog,
    DiseasePrediction,
    HealthAssessment,
    PredictionAttribution,
    Profile,
    Recommendation,
    RiskLevel,
    User,
)
from app.services.feature_mapper import FeatureMapper
from app.services.ml_engine import SUPPORTED_DISEASES, ml_engine

logger = logging.getLogger(__name__)


class PredictionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create_default_profile(self, user_id: uuid.UUID) -> Profile:
        """Ensure user has at least one active profile to link assessments."""
        res = await self.session.execute(
            select(Profile).where(Profile.user_id == user_id).order_by(Profile.created_at.asc()).limit(1)
        )
        profile = res.scalars().first()
        if profile is None:
            profile = Profile(
                id=uuid.uuid4(),
                user_id=user_id,
                display_name="Primary Profile",
            )
            self.session.add(profile)
            await self.session.commit()
            await self.session.refresh(profile)
        return profile

    async def create_prediction(
        self,
        user: Optional[User],
        disease_id: str,
        input_data: Dict[str, Any],
        model_name: str = "tabicl",
        profile_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: str = "-",
    ) -> Dict[str, Any]:
        """
        Mode B: Execute single disease model prediction, save to database, and return formatted response.
        Persists to database for both authenticated users (linked to profile) and guest sessions.
        """
        # Execute real ML inference
        pred_result = ml_engine.predict(disease_id, input_data, model_name=model_name)

        if user is not None and profile_id is None:
            profile = await self.get_or_create_default_profile(user.id)
            profile_id = profile.id

        # 1. Health Assessment record
        assessment_id = uuid.uuid4()
        assessment = HealthAssessment(
            id=assessment_id,
            profile_id=profile_id,
            assessment_version="1.0",
            assessment_mode="individual",
            input_data=input_data,
        )
        self.session.add(assessment)

        # 2. Disease Prediction record
        risk_enum = (
            RiskLevel.HIGH
            if pred_result["risk_level"] == "HIGH"
            else (RiskLevel.MODERATE if pred_result["risk_level"] == "MODERATE" else RiskLevel.LOW)
        )
        prediction_id = uuid.uuid4()
        prediction = DiseasePrediction(
            id=prediction_id,
            assessment_id=assessment_id,
            disease_code=pred_result["disease_code"],
            model_name=pred_result["model_name"],
            model_version=pred_result["model_version"],
            raw_probability=pred_result["raw_probability"],
            calibrated_probability=pred_result["calibrated_probability"],
            risk_level=risk_enum,
        )
        self.session.add(prediction)

        # 3. Prediction Attributions
        for attr in pred_result["attributions"]:
            pa = PredictionAttribution(
                id=uuid.uuid4(),
                prediction_id=prediction_id,
                feature_name=attr["feature_name"],
                feature_value=str(attr["feature_value"]),
                attribution_value=attr["attribution_value"],
            )
            self.session.add(pa)

        # 4. Recommendations
        for rec in pred_result["recommendations"]:
            r = Recommendation(
                id=uuid.uuid4(),
                prediction_id=prediction_id,
                title=rec["title"],
                description=rec["description"],
                priority=rec["priority"],
            )
            self.session.add(r)

        # 5. Audit Log (if user is authenticated)
        if user is not None:
            audit = AuditLog(
                id=uuid.uuid4(),
                user_id=user.id,
                action="HEALTH_ASSESSMENT_PREDICTION_CREATED",
                resource_type="disease_predictions",
                resource_id=str(prediction_id),
                event_metadata={
                    "disease_code": pred_result["disease_code"],
                    "risk_level": pred_result["risk_level"],
                    "model_name": pred_result["model_name"],
                    "request_id": request_id,
                },
                ip_address=ip_address,
                user_agent=user_agent,
            )
            self.session.add(audit)

        await self.session.commit()

        pred_result["prediction_id"] = str(prediction_id)
        pred_result["assessment_id"] = str(assessment_id)
        pred_result["assessment_mode"] = "individual"
        pred_result["created_at"] = datetime.now(timezone.utc).isoformat()
        pred_result["input_data"] = input_data
        return pred_result

    async def create_complete_assessment(
        self,
        user: Optional[User],
        input_data: Dict[str, Any],
        model_name: str = "tabicl",
        profile_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: str = "-",
    ) -> Dict[str, Any]:
        """
        Mode A: Execute unified full-panel multi-disease risk assessment across all 10 diseases.
        - Maps unified inputs to each disease's specific YAML features using FeatureMapper.
        - Runs real tabular foundation models (TabICLv2 or TabPFN).
        - Saves one parent HealthAssessment record (mode='combined').
        - Saves all 10 DiseasePrediction records linked to the parent assessment.
        - Saves feature attributions, recommendations, and audit logs.
        """
        results: List[Dict[str, Any]] = []
        high_risk_count = 0
        moderate_risk_count = 0
        low_risk_count = 0
        highest_risk_disease: Optional[str] = None
        highest_risk_prob = -1.0

        for disease_id in SUPPORTED_DISEASES:
            mapped_data = FeatureMapper.map_for_disease(disease_id, input_data)
            try:
                pred = ml_engine.predict(disease_id, mapped_data, model_name=model_name)
                pred["status"] = "success"
                prob = pred["raw_probability"]
                if prob > highest_risk_prob:
                    highest_risk_prob = prob
                    highest_risk_disease = pred["disease_name"]

                r_level = pred["risk_level"]
                if r_level == "HIGH":
                    high_risk_count += 1
                elif r_level == "MODERATE":
                    moderate_risk_count += 1
                else:
                    low_risk_count += 1

                results.append(pred)
            except Exception as e:
                logger.error("Prediction failed for %s: %s", disease_id, e)
                results.append({
                    "disease_code": disease_id.upper(),
                    "disease_name": disease_id.replace("_", " ").title(),
                    "model_name": "Unavailable",
                    "model_version": "None",
                    "raw_probability": 0.0,
                    "calibrated_probability": 0.0,
                    "risk_percentage": 0.0,
                    "risk_level": "UNKNOWN",
                    "status": "unavailable",
                    "error_message": f"Model for {disease_id} is temporarily unavailable: {str(e)}",
                    "attributions": [],
                    "recommendations": [],
                })

        parent_assessment_id = uuid.uuid4()
        now_utc = datetime.now(timezone.utc)

        if user is not None and profile_id is None:
            profile = await self.get_or_create_default_profile(user.id)
            profile_id = profile.id

        # 1. Parent Health Assessment record
        assessment = HealthAssessment(
            id=parent_assessment_id,
            profile_id=profile_id,
            assessment_version="1.0",
            assessment_mode="combined",
            input_data=input_data,
            created_at=now_utc,
        )
        self.session.add(assessment)

        # 2. Associated 10 Disease Predictions & Attributions
        for r in results:
            if r.get("status") != "success":
                continue
            risk_enum = (
                RiskLevel.HIGH
                if r["risk_level"] == "HIGH"
                else (RiskLevel.MODERATE if r["risk_level"] == "MODERATE" else RiskLevel.LOW)
            )
            pred_id = uuid.uuid4()
            r["prediction_id"] = str(pred_id)
            r["assessment_id"] = str(parent_assessment_id)

            prediction = DiseasePrediction(
                id=pred_id,
                assessment_id=parent_assessment_id,
                disease_code=r["disease_code"],
                model_name=r["model_name"],
                model_version=r["model_version"],
                raw_probability=r["raw_probability"],
                calibrated_probability=r["calibrated_probability"],
                risk_level=risk_enum,
                created_at=now_utc,
            )
            self.session.add(prediction)

            for attr in r.get("attributions", []):
                pa = PredictionAttribution(
                    id=uuid.uuid4(),
                    prediction_id=pred_id,
                    feature_name=attr["feature_name"],
                    feature_value=str(attr["feature_value"]),
                    attribution_value=attr["attribution_value"],
                    created_at=now_utc,
                )
                self.session.add(pa)

            for rec in r.get("recommendations", []):
                rec_obj = Recommendation(
                    id=uuid.uuid4(),
                    prediction_id=pred_id,
                    title=rec["title"],
                    description=rec["description"],
                    priority=rec["priority"],
                    created_at=now_utc,
                )
                self.session.add(rec_obj)

        # 3. Audit Log (if user authenticated)
        if user is not None:
            audit = AuditLog(
                id=uuid.uuid4(),
                user_id=user.id,
                action="HEALTH_ASSESSMENT_COMPLETE_CREATED",
                resource_type="health_assessments",
                resource_id=str(parent_assessment_id),
                event_metadata={
                    "diseases_count": len(results),
                    "high_risk_count": high_risk_count,
                    "moderate_risk_count": moderate_risk_count,
                    "low_risk_count": low_risk_count,
                    "model_name": model_name,
                    "request_id": request_id,
                },
                ip_address=ip_address,
                user_agent=user_agent,
            )
            self.session.add(audit)

        await self.session.commit()

        return {
            "assessment_id": str(parent_assessment_id),
            "assessment_mode": "combined",
            "created_at": now_utc.isoformat(),
            "diseases_evaluated": len(results),
            "summary": {
                "high_risk_count": high_risk_count,
                "moderate_risk_count": moderate_risk_count,
                "low_risk_count": low_risk_count,
                "highest_risk_disease": highest_risk_disease,
                "highest_risk_percentage": round(highest_risk_prob * 100, 2) if highest_risk_prob >= 0 else 0.0,
            },
            "results": results,
            "input_data": input_data,
            "disclaimer": (
                "IMPORTANT CLINICAL SAFETY NOTICE: MediRisk 2.0 is an academic and research prototyping platform. "
                "Assessments are derived from synthetic tabular foundation models and DO NOT constitute a medical diagnosis, "
                "clinical prognosis, or treatment plan. Always consult a licensed healthcare physician."
            ),
        }

    async def get_complete_assessment(
        self, assessment_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """Fetch combined assessment with all associated disease prediction records."""
        stmt = (
            select(HealthAssessment)
            .options(
                selectinload(HealthAssessment.predictions).selectinload(DiseasePrediction.attributions),
                selectinload(HealthAssessment.predictions).selectinload(DiseasePrediction.recommendations),
            )
            .where(HealthAssessment.id == assessment_id)
        )
        res = await self.session.execute(stmt)
        assessment = res.scalar_one_or_none()
        if not assessment:
            raise NotFoundError("HealthAssessment")

        results = []
        high_risk_count = 0
        moderate_risk_count = 0
        low_risk_count = 0
        highest_risk_disease = None
        highest_risk_prob = -1.0

        for pred in sorted(assessment.predictions, key=lambda x: x.disease_code):
            prob = float(pred.raw_probability)
            d_name = pred.disease_code.replace("_", " ").title()
            if prob > highest_risk_prob:
                highest_risk_prob = prob
                highest_risk_disease = d_name

            r_level = pred.risk_level.value if hasattr(pred.risk_level, "value") else str(pred.risk_level)
            if r_level == "HIGH":
                high_risk_count += 1
            elif r_level == "MODERATE":
                moderate_risk_count += 1
            else:
                low_risk_count += 1

            results.append({
                "prediction_id": str(pred.id),
                "assessment_id": str(assessment.id),
                "disease_code": pred.disease_code,
                "disease_name": d_name,
                "model_name": pred.model_name,
                "model_version": pred.model_version,
                "raw_probability": prob,
                "calibrated_probability": float(pred.calibrated_probability or prob),
                "risk_percentage": round(prob * 100, 2),
                "risk_level": r_level,
                "status": "success",
                "attributions": [
                    {
                        "feature_name": a.feature_name,
                        "feature_label": a.feature_name.replace("_", " ").title(),
                        "feature_value": a.feature_value,
                        "attribution_value": float(a.attribution_value),
                        "impact": "INCREASES_RISK" if float(a.attribution_value) > 0.05 else ("PROTECTIVE" if float(a.attribution_value) < -0.05 else "NEUTRAL"),
                    }
                    for a in pred.attributions
                ],
                "recommendations": [
                    {
                        "title": r.title,
                        "description": r.description,
                        "priority": r.priority,
                    }
                    for r in sorted(pred.recommendations, key=lambda x: x.priority)
                ],
            })

        return {
            "assessment_id": str(assessment.id),
            "assessment_mode": assessment.assessment_mode,
            "created_at": assessment.created_at.isoformat(),
            "diseases_evaluated": len(results),
            "summary": {
                "high_risk_count": high_risk_count,
                "moderate_risk_count": moderate_risk_count,
                "low_risk_count": low_risk_count,
                "highest_risk_disease": highest_risk_disease,
                "highest_risk_percentage": round(highest_risk_prob * 100, 2) if highest_risk_prob >= 0 else 0.0,
            },
            "results": results,
            "input_data": assessment.input_data,
            "disclaimer": (
                "IMPORTANT CLINICAL SAFETY NOTICE: MediRisk 2.0 is an academic and research prototyping platform. "
                "Assessments are derived from synthetic tabular foundation models and DO NOT constitute a medical diagnosis, "
                "clinical prognosis, or treatment plan. Always consult a licensed healthcare physician."
            ),
        }

    async def get_user_history(
        self,
        user_id: uuid.UUID,
        disease_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Fetch past predictions belonging to any profile of this user."""
        query = (
            select(DiseasePrediction, HealthAssessment)
            .join(HealthAssessment, DiseasePrediction.assessment_id == HealthAssessment.id)
            .join(Profile, HealthAssessment.profile_id == Profile.id)
            .where(Profile.user_id == user_id)
            .order_by(desc(DiseasePrediction.created_at))
        )

        if disease_filter:
            query = query.where(DiseasePrediction.disease_code == disease_filter.upper())

        query = query.limit(limit).offset(offset)
        res = await self.session.execute(query)
        rows = res.all()

        history = []
        for pred, assess in rows:
            history.append({
                "id": str(pred.id),
                "assessment_id": str(assess.id),
                "assessment_mode": getattr(assess, "assessment_mode", "individual"),
                "disease_code": pred.disease_code,
                "disease_name": pred.disease_code.replace("_", " ").title(),
                "model_name": pred.model_name,
                "model_version": pred.model_version,
                "raw_probability": float(pred.raw_probability),
                "risk_percentage": round(float(pred.raw_probability) * 100, 2),
                "risk_level": pred.risk_level.value if hasattr(pred.risk_level, "value") else str(pred.risk_level),
                "created_at": pred.created_at.isoformat(),
                "input_data": assess.input_data,
            })
        return history

    async def get_prediction_detail(
        self, prediction_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """Fetch detailed prediction record including attributions and recommendations."""
        query = (
            select(DiseasePrediction)
            .options(
                selectinload(DiseasePrediction.assessment),
                selectinload(DiseasePrediction.attributions),
                selectinload(DiseasePrediction.recommendations),
            )
            .where(DiseasePrediction.id == prediction_id)
        )
        res = await self.session.execute(query)
        pred = res.scalar_one_or_none()
        if not pred:
            raise NotFoundError("DiseasePrediction")

        return {
            "prediction_id": str(pred.id),
            "assessment_id": str(pred.assessment_id),
            "assessment_mode": getattr(pred.assessment, "assessment_mode", "individual") if pred.assessment else "individual",
            "disease_code": pred.disease_code,
            "disease_name": pred.disease_code.replace("_", " ").title(),
            "model_name": pred.model_name,
            "model_version": pred.model_version,
            "raw_probability": float(pred.raw_probability),
            "calibrated_probability": float(pred.calibrated_probability or pred.raw_probability),
            "risk_percentage": round(float(pred.raw_probability) * 100, 2),
            "risk_level": pred.risk_level.value if hasattr(pred.risk_level, "value") else str(pred.risk_level),
            "created_at": pred.created_at.isoformat(),
            "input_data": pred.assessment.input_data if pred.assessment else {},
            "attributions": [
                {
                    "feature_name": a.feature_name,
                    "feature_label": a.feature_name.replace("_", " ").title(),
                    "feature_value": a.feature_value,
                    "attribution_value": float(a.attribution_value),
                    "impact": "INCREASES_RISK" if float(a.attribution_value) > 0.05 else ("PROTECTIVE" if float(a.attribution_value) < -0.05 else "NEUTRAL"),
                }
                for a in pred.attributions
            ],
            "recommendations": [
                {
                    "title": r.title,
                    "description": r.description,
                    "priority": r.priority,
                }
                for r in sorted(pred.recommendations, key=lambda x: x.priority)
            ],
            "disclaimer": (
                "IMPORTANT CLINICAL SAFETY NOTICE: MediRisk 2.0 is an academic and research prototyping platform. "
                "Assessments are derived from synthetic tabular datasets and DO NOT constitute a medical diagnosis, "
                "clinical prognosis, or definitive treatment plan. Always consult a licensed healthcare physician."
            ),
        }

    async def get_analytics_overview(self, user_id: Optional[uuid.UUID] = None) -> Dict[str, Any]:
        """Aggregate statistical summary across diseases and predictions."""
        base_query = (
            select(
                DiseasePrediction.disease_code,
                DiseasePrediction.risk_level,
                func.count(DiseasePrediction.id),
                func.avg(DiseasePrediction.raw_probability),
            )
            .join(HealthAssessment, DiseasePrediction.assessment_id == HealthAssessment.id)
            .join(Profile, HealthAssessment.profile_id == Profile.id)
        )

        if user_id:
            base_query = base_query.where(Profile.user_id == user_id)

        base_query = base_query.group_by(DiseasePrediction.disease_code, DiseasePrediction.risk_level)
        res = await self.session.execute(base_query)
        rows = res.all()

        disease_stats: Dict[str, Dict[str, Any]] = {}
        risk_tier_counts = {"LOW": 0, "MODERATE": 0, "HIGH": 0}
        total_predictions = 0

        for disease_code, risk_level, count, avg_prob in rows:
            r_str = risk_level.value if hasattr(risk_level, "value") else str(risk_level)
            risk_tier_counts[r_str] = risk_tier_counts.get(r_str, 0) + count
            total_predictions += count

            if disease_code not in disease_stats:
                disease_stats[disease_code] = {
                    "disease_code": disease_code,
                    "disease_name": disease_code.replace("_", " ").title(),
                    "total": 0,
                    "low": 0,
                    "moderate": 0,
                    "high": 0,
                    "avg_probability": 0.0,
                }
            disease_stats[disease_code]["total"] += count
            if r_str == "LOW":
                disease_stats[disease_code]["low"] += count
            elif r_str == "MODERATE":
                disease_stats[disease_code]["moderate"] += count
            elif r_str == "HIGH":
                disease_stats[disease_code]["high"] += count
            disease_stats[disease_code]["avg_probability"] = round(float(avg_prob or 0), 4)

        return {
            "total_assessments": total_predictions,
            "risk_tier_distribution": risk_tier_counts,
            "disease_distribution": list(disease_stats.values()),
            "benchmark_summary": ml_engine.benchmark_summary,
        }
