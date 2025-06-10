import os
import tensorflow as tf
import requests

# ✅ رابط تحميل النموذج – لازم يكون مباشر من Cloud Storage
MODEL_URL = "https://storage.googleapis.com/YOUR_BUCKET_NAME/multitask_lab_reports_model.h5"
MODEL_PATH = "/app/models/multitask_lab_reports_model.h5"

# ✅ تأكد إن الموديل موجود، لو مش موجود يتم تحميله
if not os.path.exists(MODEL_PATH):
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    print("Downloading model...")
    response = requests.get(MODEL_URL)
    if response.status_code != 200:
        raise ValueError(f"Failed to download model. Status code: {response.status_code}")
    with open(MODEL_PATH, "wb") as f:
        f.write(response.content)
    if os.path.getsize(MODEL_PATH) < 1000:
        raise ValueError("Downloaded model file appears to be invalid or corrupted.")
    print("Model downloaded.")

# ✅ تحميل النموذج
print("Loading model...")
model = tf.keras.models.load_model(MODEL_PATH)
print("Model loaded.")


# ✅ FastAPI setup
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ✅ استدعاء الروترات
from routers import (
    users, pending_approvals, doctor_assignments,
    surgeries, bloodbiomarkers, measurements, radiology, hypertension,
    medications, diagnoses, allergies, family_history,
    emergency_contacts, risk_assessment, admin, user_role, auth, facilities, qrcode, send_email
)

app = FastAPI(title="MediGO Backend", version="1.0")

# ✅ إعداد CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ تسجيل الروترات
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(users.router)
app.include_router(qrcode.router)
app.include_router(pending_approvals.router)
app.include_router(doctor_assignments.router)
app.include_router(facilities.router)
app.include_router(surgeries.router)
app.include_router(bloodbiomarkers.router)
app.include_router(measurements.router)
app.include_router(radiology.router)
app.include_router(hypertension.router)
app.include_router(medications.router)
app.include_router(diagnoses.router)
app.include_router(allergies.router)
app.include_router(family_history.router)
app.include_router(emergency_contacts.router)
app.include_router(risk_assessment.router)
app.include_router(user_role.router)
app.include_router(send_email.router)

# ✅ مسار اختباري
@app.get("/")
def root():
    return {"message": "Welcome to the MediGO FastAPI Backend"}

# ✅ السطر المسؤول عن تشغيل التطبيق في Cloud Run أو محليًا
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))  # Cloud Run will pass PORT=8080
    uvicorn.run("main:app", host="0.0.0.0", port=port)
