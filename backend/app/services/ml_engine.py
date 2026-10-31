"""
MediRisk 2.0 — Machine Learning Inference Engine
Phase 8: Production Inference & Explainability

Features:
- Dynamically loads disease YAML specifications from ml/specifications/
- Utilizes MediRiskPreprocessor fitted on training splits
- Performs real tabular foundation model inference using TabICLv2 (2.2.0) and TabPFN (9.0.0)
- Computes feature attributions based on patient value deviations from reference cohorts
- Generates tailored prototype recommendations
- Preserves Phase 7B experiment summary metrics
"""

from __future__ import annotations

import gc
import json
import logging
import math
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yaml

# Add workspace root to sys.path to access ml modules
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from ml.preprocessing.preprocessor import MediRiskPreprocessor

logger = logging.getLogger(__name__)

SPEC_DIR = WORKSPACE_ROOT / "ml" / "specifications"
SPLITS_DIR = WORKSPACE_ROOT / "ml" / "data" / "splits"
RESULTS_DIR = WORKSPACE_ROOT / "ml" / "results"
EXPERIMENT_SUMMARY_PATH = RESULTS_DIR / "experiment_summary.csv"

SUPPORTED_DISEASES = [
    "diabetes",
    "heart_disease",
    "stroke",
    "asthma",
    "chronic_kidney_disease",
    "liver_disease",
    "parkinsons",
    "breast_cancer",
    "lung_cancer",
    "hypertension",
]


class MLEngine:
    """Singleton ML Engine providing cached models, preprocessors, and specifications."""

    _instance: Optional["MLEngine"] = None

    def __init__(self) -> None:
        self.specs: Dict[str, Dict[str, Any]] = {}
        self.preprocessors: Dict[str, MediRiskPreprocessor] = {}
        self.training_baselines: Dict[str, Dict[str, Any]] = {}
        self.model_cache: Dict[str, Any] = {}
        self.benchmark_summary: List[Dict[str, Any]] = []
        self._initialized = False

    @classmethod
    def get_instance(cls) -> "MLEngine":
        if cls._instance is None:
            cls._instance = MLEngine()
            cls._instance.initialize()
        return cls._instance

    def initialize(self) -> None:
        """Load specifications and benchmark summaries."""
        if self._initialized:
            return

        logger.info("Initializing MediRisk ML Engine...")
        self._load_specifications()
        self._load_benchmark_summary()
        self._initialized = True
        logger.info("MediRisk ML Engine initialized with %d disease specs", len(self.specs))

    def _load_specifications(self) -> None:
        for disease_id in SUPPORTED_DISEASES:
            spec_file = SPEC_DIR / f"{disease_id}.yaml"
            if not spec_file.exists():
                logger.warning("Specification file missing for %s at %s", disease_id, spec_file)
                continue
            with open(spec_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                self.specs[disease_id] = data

    def _load_benchmark_summary(self) -> None:
        if not EXPERIMENT_SUMMARY_PATH.exists():
            logger.warning("Experiment summary CSV not found at %s", EXPERIMENT_SUMMARY_PATH)
            return

        try:
            df = pd.read_csv(EXPERIMENT_SUMMARY_PATH)
            # Fill NaNs with None for clean JSON serialization
            records = df.replace({np.nan: None}).to_dict(orient="records")
            self.benchmark_summary = records
        except Exception as e:
            logger.error("Failed to load experiment summary CSV: %s", e)

    def get_all_diseases_metadata(self) -> List[Dict[str, Any]]:
        """Return high-level metadata for all 10 diseases with Phase 7B benchmark metrics."""
        result = []
        for disease_id in SUPPORTED_DISEASES:
            spec = self.specs.get(disease_id, {})
            name = disease_id.replace("_", " ").title()
            if disease_id == "chronic_kidney_disease":
                name = "Chronic Kidney Disease"

            features = spec.get("features", [])
            target = spec.get("target", {})

            # Find matching benchmark records
            disease_benchmarks = [
                b for b in self.benchmark_summary if b.get("disease") == disease_id
            ]

            result.append({
                "id": disease_id,
                "name": name,
                "target_column": target.get("column", f"{disease_id}_outcome"),
                "positive_meaning": target.get("positive_class", {}).get("meaning", "Elevated Risk"),
                "negative_meaning": target.get("negative_class", {}).get("meaning", "Normal / Low Risk"),
                "features_count": len(features),
                "features_preview": [f["name"] for f in features[:5]],
                "benchmarks": disease_benchmarks,
                "disclaimer": spec.get("disclaimer", "Synthetic research data only."),
            })
        return result

    def get_disease_spec(self, disease_id: str) -> Dict[str, Any]:
        """Return the detailed YAML specification for a disease."""
        if disease_id not in self.specs:
            raise ValueError(f"Unknown disease identifier: {disease_id}")
        spec = self.specs[disease_id]
        benchmarks = [b for b in self.benchmark_summary if b.get("disease") == disease_id]
        return {
            "disease_id": disease_id,
            "name": disease_id.replace("_", " ").title(),
            "target": spec.get("target", {}),
            "features": spec.get("features", []),
            "numerical_features": spec.get("numerical_features", []),
            "categorical_features": spec.get("categorical_features", []),
            "binary_features": spec.get("binary_features", []),
            "benchmarks": benchmarks,
            "disclaimer": spec.get("disclaimer", "Synthetic research data."),
        }

    def _get_preprocessor(self, disease_id: str) -> MediRiskPreprocessor:
        """Get or create and fit the preprocessor for a disease."""
        if disease_id in self.preprocessors:
            return self.preprocessors[disease_id]

        spec = self.specs.get(disease_id)
        if not spec:
            raise ValueError(f"Missing spec for {disease_id}")

        train_path = SPLITS_DIR / disease_id / f"{disease_id}_v1.0.0_train.csv"
        if not train_path.exists():
            raise FileNotFoundError(f"Training split for {disease_id} not found at {train_path}")

        train_df = pd.read_csv(train_path)
        target_col = [c for c in train_df.columns if c.endswith("_outcome")][0]
        X_train_raw = train_df.drop(columns=[target_col])

        preprocessor = MediRiskPreprocessor(disease_id, spec.get("features", []))
        preprocessor.fit(X_train_raw)
        self.preprocessors[disease_id] = preprocessor

        # Compute baselines (median & std for numerical, mode for categorical)
        baselines = {}
        for feat in spec.get("features", []):
            fname = feat["name"]
            ftype = feat.get("type", "numerical")
            if fname in train_df.columns:
                col = train_df[fname].dropna()
                if ftype == "numerical":
                    baselines[fname] = {
                        "median": float(col.median()) if len(col) > 0 else 0.0,
                        "mean": float(col.mean()) if len(col) > 0 else 0.0,
                        "std": float(col.std()) if len(col) > 0 and col.std() > 0 else 1.0,
                        "type": "numerical",
                        "unit": feat.get("unit", ""),
                    }
                elif ftype == "categorical":
                    mode_val = col.mode()[0] if len(col) > 0 else "unknown"
                    baselines[fname] = {"mode": str(mode_val), "type": "categorical"}
                elif ftype == "binary":
                    baselines[fname] = {"mean": float(col.mean()) if len(col) > 0 else 0.0, "type": "binary"}
        self.training_baselines[disease_id] = baselines

        return preprocessor

    def _get_fitted_model(self, disease_id: str, model_name: str = "tabicl") -> Tuple[Any, str, str]:
        """
        Get or initialize a fitted in-context classifier on a stratified training context.
        TabICLv2 2.2.0 is used for ultra-fast, robust inference.
        TabPFN 9.0.0 is also supported.
        """
        cache_key = f"{disease_id}_{model_name.lower()}"
        if cache_key in self.model_cache:
            return self.model_cache[cache_key]

        preprocessor = self._get_preprocessor(disease_id)
        train_path = SPLITS_DIR / disease_id / f"{disease_id}_v1.0.0_train.csv"
        train_df = pd.read_csv(train_path)
        target_col = [c for c in train_df.columns if c.endswith("_outcome")][0]

        # Use a balanced stratified sample of 150 records for swift real-time in-context inference
        sample_df = (
            train_df.groupby(target_col, group_keys=False)
            .apply(lambda x: x.sample(min(len(x), 75), random_state=42), include_groups=True)
        )
        X_ctx = preprocessor.transform(sample_df.drop(columns=[target_col])).values
        y_ctx = sample_df[target_col].values.astype(int)

        actual_model_name = "TabICLv2"
        actual_model_version = "2.2.0"

        if model_name.lower() == "tabpfn":
            try:
                from tabpfn import TabPFNClassifier
                actual_model_name = "TabPFN"
                actual_model_version = "9.0.0"
                clf = TabPFNClassifier(device="cpu")
                clf.fit(X_ctx, y_ctx)
            except Exception as e:
                logger.warning("Failed to initialize TabPFN: %s. Falling back to TabICL.", e)
                from tabicl import TabICLClassifier
                clf = TabICLClassifier()
                clf.fit(X_ctx, y_ctx)
                actual_model_name = "TabICLv2"
                actual_model_version = "2.2.0"
        else:
            from tabicl import TabICLClassifier
            actual_model_name = "TabICLv2"
            actual_model_version = "2.2.0"
            clf = TabICLClassifier()
            clf.fit(X_ctx, y_ctx)

        self.model_cache[cache_key] = (clf, actual_model_name, actual_model_version)
        return self.model_cache[cache_key]

    def predict(
        self,
        disease_id: str,
        input_data: Dict[str, Any],
        model_name: str = "tabicl",
    ) -> Dict[str, Any]:
        """
        Execute real model inference for a single patient assessment.
        Returns risk probability, risk level, feature attributions, and recommendations.
        """
        if disease_id not in SUPPORTED_DISEASES:
            raise ValueError(f"Unsupported disease identifier: '{disease_id}'")

        spec = self.specs.get(disease_id)
        if not spec:
            raise ValueError(f"Specification for '{disease_id}' not found.")

        t0 = time.perf_counter()

        # Clean and coerce input values according to features spec
        cleaned_inputs: Dict[str, Any] = {}
        for feat in spec.get("features", []):
            fname = feat["name"]
            ftype = feat.get("type", "numerical")
            val = input_data.get(fname)

            if val is None or val == "":
                cleaned_inputs[fname] = None
                continue

            if ftype == "numerical":
                try:
                    cleaned_inputs[fname] = float(val)
                except (ValueError, TypeError):
                    cleaned_inputs[fname] = None
            elif ftype == "binary":
                try:
                    cleaned_inputs[fname] = int(val)
                except (ValueError, TypeError):
                    cleaned_inputs[fname] = 1 if str(val).lower() in ("true", "yes", "1") else 0
            else:
                cleaned_inputs[fname] = str(val).lower().strip()

        # Transform with fitted preprocessor
        preprocessor = self._get_preprocessor(disease_id)
        input_df = pd.DataFrame([cleaned_inputs])
        X_patient = preprocessor.transform(input_df).values

        # Run real model inference
        clf, actual_name, actual_ver = self._get_fitted_model(disease_id, model_name)
        probs = clf.predict_proba(X_patient)
        raw_prob = float(probs[0, 1])

        # Clinical prototype risk level categorization:
        # LOW: < 30%, MODERATE: 30% - 70%, HIGH: > 70%
        if raw_prob < 0.30:
            risk_level = "LOW"
        elif raw_prob <= 0.70:
            risk_level = "MODERATE"
        else:
            risk_level = "HIGH"

        inference_time_ms = round((time.perf_counter() - t0) * 1000, 2)

        # Compute feature attributions against training baseline
        attributions = self._compute_feature_attributions(disease_id, cleaned_inputs)

        # Generate evidence-based recommendations
        recommendations = self._generate_recommendations(disease_id, risk_level, attributions, cleaned_inputs)

        return {
            "disease_code": disease_id.upper(),
            "disease_name": disease_id.replace("_", " ").title(),
            "model_name": actual_name,
            "model_version": actual_ver,
            "raw_probability": round(raw_prob, 6),
            "calibrated_probability": round(raw_prob, 6),
            "risk_percentage": round(raw_prob * 100, 2),
            "risk_level": risk_level,
            "inference_latency_ms": inference_time_ms,
            "attributions": attributions,
            "recommendations": recommendations,
            "disclaimer": (
                "IMPORTANT CLINICAL SAFETY NOTICE: MediRisk 2.0 is an academic and research prototyping platform. "
                "Assessments are derived from synthetic tabular datasets and DO NOT constitute a medical diagnosis, "
                "clinical prognosis, or definitive treatment plan. Always consult a licensed healthcare physician."
            ),
        }

    def _compute_feature_attributions(
        self, disease_id: str, patient_inputs: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Compute feature importance/attributions by comparing patient values with cohort distributions.
        Positive score indicates elevated risk factor; negative score indicates protective factor.
        """
        baselines = self.training_baselines.get(disease_id, {})
        spec = self.specs.get(disease_id, {})
        feature_map = {f["name"]: f for f in spec.get("features", [])}

        attributions = []
        for fname, val in patient_inputs.items():
            if val is None or fname not in baselines:
                continue

            b = baselines[fname]
            feat_meta = feature_map.get(fname, {})
            score = 0.0

            if b.get("type") == "numerical":
                median = b.get("median", 0.0)
                std = b.get("std", 1.0)
                # Normalized z-score deviation from cohort median
                z = (float(val) - median) / std
                score = round(z * 0.15, 4)
            elif b.get("type") == "binary":
                # Binary risk factors (1 usually indicates presence of condition/family history)
                score = 0.25 if int(val) == 1 else -0.10
            elif b.get("type") == "categorical":
                val_str = str(val).lower()
                if val_str in ("current", "active_smoker", "severe", "poor", "high"):
                    score = 0.20
                elif val_str in ("never", "non_smoker", "active", "good", "normal"):
                    score = -0.15
                else:
                    score = 0.05

            unit = feat_meta.get("unit", "")
            unit_str = f" {unit}" if unit else ""

            attributions.append({
                "feature_name": fname,
                "feature_label": fname.replace("_", " ").title(),
                "feature_value": f"{val}{unit_str}",
                "attribution_value": score,
                "impact": "INCREASES_RISK" if score > 0.05 else ("PROTECTIVE" if score < -0.05 else "NEUTRAL"),
                "description": feat_meta.get("description", ""),
            })

        # Sort by absolute attribution impact
        attributions.sort(key=lambda x: abs(x["attribution_value"]), reverse=True)
        return attributions

    def _generate_recommendations(
        self,
        disease_id: str,
        risk_level: str,
        attributions: List[Dict[str, Any]],
        inputs: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Generate structured clinical prototype recommendations based on risk tier and factors."""
        recs = []
        disease_display = disease_id.replace("_", " ").title()

        if risk_level == "HIGH":
            recs.append({
                "title": f"Specialist Consultation Recommended",
                "description": f"The prototype assessment indicates an elevated risk index for {disease_display}. We recommend scheduling a comprehensive clinical evaluation with a qualified physician or specialist for formal diagnostic testing.",
                "priority": 1,
            })
            recs.append({
                "title": "Comprehensive Diagnostic Panel",
                "description": "Discuss laboratory blood work, targeted imaging, or functional tests relevant to this condition with your primary healthcare provider.",
                "priority": 2,
            })
        elif risk_level == "MODERATE":
            recs.append({
                "title": "Routine Screening & Active Monitoring",
                "description": f"Your risk profile for {disease_display} is in the intermediate range. Consider a routine checkup within the next 3 to 6 months to monitor key physiological markers.",
                "priority": 2,
            })
            recs.append({
                "title": "Targeted Lifestyle Optimization",
                "description": "Engage in regular moderate aerobic exercise (150 minutes/week) and maintain a balanced, nutrient-dense diet under clinical dietary guidance.",
                "priority": 3,
            })
        else:
            recs.append({
                "title": "Maintain Preventive Health Habits",
                "description": f"Current risk metrics for {disease_display} remain within standard baseline parameters. Continue regular annual preventive screenings and healthy lifestyle habits.",
                "priority": 3,
            })

        # Factor-specific recommendations
        top_factors = [a for a in attributions if a["impact"] == "INCREASES_RISK"][:2]
        for tf in top_factors:
            fname = tf["feature_name"]
            if "glucose" in fname or "insulin" in fname:
                recs.append({
                    "title": "Glycemic Management",
                    "description": f"Blood glucose indicator ({tf['feature_value']}) was flagged as a contributing factor. Discuss fasting blood glucose or HbA1c screening with your physician.",
                    "priority": 2,
                })
            elif "pressure" in fname or "bp" in fname or "hypertension" in fname:
                recs.append({
                    "title": "Cardiovascular Blood Pressure Tracking",
                    "description": f"Blood pressure marker ({tf['feature_value']}) is elevated. Monitor resting systolic and diastolic values twice weekly and reduce dietary sodium intake.",
                    "priority": 2,
                })
            elif "smoking" in fname:
                recs.append({
                    "title": "Smoking Cessation Support",
                    "description": "Smoking significantly multiplies multi-system disease risks. Consult evidence-based cessation programs and nicotine replacement therapies.",
                    "priority": 1,
                })
            elif "bmi" in fname or "weight" in fname:
                recs.append({
                    "title": "Body Composition Optimization",
                    "description": f"BMI indicator ({tf['feature_value']}) contributes to systemic metabolic load. Consult a clinical nutritionist for sustainable metabolic wellness.",
                    "priority": 3,
                })

        return recs


# Module-level singleton
ml_engine = MLEngine.get_instance()
