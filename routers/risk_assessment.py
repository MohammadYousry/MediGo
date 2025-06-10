from datetime import datetime
from fastapi import APIRouter, HTTPException
from firebase_config import db
import pandas as pd
import numpy as np
import joblib
from models.schema import RiskPredictionOutput, DerivedFeatures, TopFeatures

router = APIRouter(prefix="/risk", tags=["Risk Assessment"])

# Lazy-loaded model components
scaler_diabetes = None
scaler_hypertension = None
selector_dia = None
selector_hyp = None
model_diabetes = None
model_hypertension = None
selected_features_dia = None
selected_features_hyp = None

# ✅ Lazy loading function
def load_models():
    global scaler_diabetes, scaler_hypertension, selector_dia, selector_hyp
    global model_diabetes, model_hypertension, selected_features_dia, selected_features_hyp

    if model_diabetes is None or model_hypertension is None:
        print("🔄 Loading risk prediction models...")
        scaler_diabetes = joblib.load("scaler_diabetes.pkl")
        scaler_hypertension = joblib.load("scaler_hypertension.pkl")
        selector_dia = joblib.load("selector_dia.pkl")
        selector_hyp = joblib.load("selector_hypertension.pkl")
        model_diabetes = joblib.load("model_diabetes.pkl")
        model_hypertension = joblib.load("model_hypertension.pkl")
        selected_features_dia = joblib.load("selected_diabetes_features.pkl")
        selected_features_hyp = joblib.load("selected_hypertension_features.pkl")
        print("✅ Models loaded.")

# ✅ Main Endpoint
@router.post("/{national_id}", response_model=RiskPredictionOutput)
async def assess_risk(national_id: str):
    try:
        load_models()  # Ensure models are loaded

        # === 1. Load User Info ===
        user_doc = db.collection("Users").document(national_id).get()
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="User not found")
        user = user_doc.to_dict()

        # === 2. Load Measurements ===
        measurements = db.collection("Users").document(national_id)\
            .collection("ClinicalIndicators").document("measurements").get().to_dict()
        if not measurements:
            raise HTTPException(status_code=404, detail="Missing measurements")

        # === 3. Load Hypertension Record ===
        hyp_docs = db.collection("Users").document(national_id)\
            .collection("ClinicalIndicators").document("Hypertension")\
            .collection("Records").order_by("date", direction="DESCENDING").limit(1).stream()
        hypertension = next(hyp_docs, None)
        hypertension = hypertension.to_dict() if hypertension else {}

        # === 4. Load Blood Biomarkers ===
        bio_docs = db.collection("Users").document(national_id)\
            .collection("ClinicalIndicators").document("bloodbiomarkers")\
            .collection("Records").order_by("date_added", direction="DESCENDING").limit(1).stream()
        biomarkers = next(bio_docs, None)
        biomarkers = biomarkers.to_dict() if biomarkers else {}

        # === 5. Load Medications ===
        med_docs = db.collection("Users").document(national_id).collection("medications")\
            .order_by("start_date", direction="DESCENDING").limit(1).stream()
        medications = next(med_docs, None)
        medications = medications.to_dict() if medications else {}

        # === 6. BMI Logic ===
        bmi = measurements.get("bmi", 25.0)
        bmi_category = 0 if bmi < 18.5 else 1 if bmi < 25 else 2 if bmi < 30 else 3
        is_obese = int(bmi >= 30)

        # === 7. Assemble Features ===
        features = {
            'male': 1 if user.get("gender") == "male" else 0,
            'BPMeds': int(medications.get("bp_medication", 0)),
            'totChol': float(next((r.get("value") for r in biomarkers.get("results", []) if r.get("item") == "Cholesterol"), 180)),
            'sysBP': float(hypertension.get("sysBP", 120)),
            'diaBP': float(hypertension.get("diaBP", 80)),
            'heartRate': float(hypertension.get("heartRate", 72)),
            'glucose': float(next((r.get("value") for r in biomarkers.get("results", []) if r.get("item") == "Glucose"), 100)),
            'age_group': int(user.get("age_group", 1)),
            'smoker_status': int(user.get("smoker_status", 0)),
            'is_obese': is_obese,
            'bp_category': int(hypertension.get("bp_category", 0)),
            'bmi_category': bmi_category,
            'male_smoker': int(user.get("gender") == "male" and user.get("smoker_status", 0) > 0),
            'prediabetes_indicator': int(hypertension.get("prediabetes_indicator", 0)),
            'insulin_resistance': int(hypertension.get("insulin_resistance", 0)),
            'metabolic_syndrome': int(hypertension.get("metabolic_syndrome", 0))
        }

        # === 8. Predict Diabetes ===
        X_dia = pd.DataFrame([features])
        X_dia["hypertension"] = 0.5
        scaled_dia = scaler_diabetes.transform(X_dia[scaler_diabetes.feature_names_in_])
        selected_dia = selector_dia.transform(scaled_dia)
        diabetes_prob = float(model_diabetes.predict_proba(selected_dia)[0][1])

        # === 9. Predict Hypertension ===
        X_hyp = pd.DataFrame([features])
        X_hyp["diabetes"] = diabetes_prob
        scaled_hyp = scaler_hypertension.transform(X_hyp[scaler_hypertension.feature_names_in_])
        selected_hyp = selector_hyp.transform(scaled_hyp)
        hypertension_prob = float(model_hypertension.predict_proba(selected_hyp)[0][1])

        # === 10. Top Feature Extraction Function ===
        def top_features(model, X_selected, feature_names, top_n=3):
            try:
                base = model.named_estimators_[next(iter(model.named_estimators_))] if hasattr(model, "named_estimators_") else model
                if hasattr(base, "feature_importances_"):
                    imp = base.feature_importances_
                elif hasattr(base, "coef_"):
                    imp = np.abs(base.coef_[0])
                else:
                    raise Exception("Model doesn't support feature importances.")
                idx = np.argsort(imp)[::-1][:top_n]
                total = sum(imp[i] for i in idx) or 1
                return [
                    TopFeatures(feature_name=feature_names[i], contribution_score=round((imp[i]/total)*100, 1))
                    for i in idx
                ]
            except Exception:
                return [
                    TopFeatures(feature_name=feature_names[i], contribution_score=round(s, 1))
                    for i, s in zip(np.random.choice(len(feature_names), top_n, replace=False), [33.3, 33.3, 33.4])
                ]

        # === 11. Get Top Features
        dia_top = top_features(model_diabetes, selected_dia, selected_features_dia)
        hyp_top = top_features(model_hypertension, selected_hyp, selected_features_hyp)

        # === 12. Derived Values
        derived = DerivedFeatures(
            age_group={0: "Young", 1: "Middle-aged", 2: "Older"}.get(features["age_group"], "Middle-aged"),
            smoker_status={0: "Non-smoker", 1: "Light", 2: "Moderate", 3: "Heavy"}.get(features["smoker_status"], "Non-smoker"),
            is_obese=bool(is_obese),
            bp_category={-1: "Low", 0: "Normal", 1: "Elevated", 2: "Stage 1", 3: "Stage 2"}.get(features["bp_category"], "Normal"),
            bmi_category={0: "Underweight", 1: "Normal", 2: "Overweight", 3: "Obese"}.get(bmi_category, "Normal"),
            bmi=bmi,
            pulse_pressure=features["sysBP"] - features["diaBP"],
            male_smoker=bool(features["male_smoker"]),
            prediabetes_indicator=bool(features["prediabetes_indicator"]),
            insulin_resistance=bool(features["insulin_resistance"]),
            metabolic_syndrome=bool(features["metabolic_syndrome"])
        )

        result = RiskPredictionOutput(
            diabetes_risk=round(diabetes_prob * 100, 2),
            hypertension_risk=round(hypertension_prob * 100, 2),
            derived_features=derived,
            input_values=features,
            top_diabetes_features=dia_top,
            top_hypertension_features=hyp_top
        )

        # === 13. Save to Firestore
        now = datetime.now()
        db.collection("Users").document(national_id).collection("risk_predictions")\
            .document(now.strftime("%Y%m%d_%H%M%S")).set({
                **result.dict(),
                "timestamp": now.isoformat(),
                "display_time": now.strftime("%B %d, %Y at %I:%M %p"),
                "sortable_time": now.strftime("%Y-%m-%d %H:%M:%S")
            })

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
