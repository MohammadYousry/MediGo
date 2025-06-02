from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.openapi.docs import get_swagger_ui_html

# === Routers ===
from routers import (
    users, pending_approvals, doctor_assignments,
    surgeries, bloodbiomarkers, measurements, radiology, hypertension,
    medications, diagnoses, allergies, family_history,
    emergency_contacts, risk_assessment, admin, user_role, auth, facilities, qrcode,
)

app = FastAPI(title="MediGO Backend", version="1.0")

# === CORS Middleware ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Routers ===
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

# === Root Route ===
@app.get("/")
def root():
    return {"message": "Welcome to the MediGO FastAPI Backend"}

# === Swagger Auth Protection ===
security = HTTPBasic()

def verify(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = credentials.username == "admin"
    correct_password = credentials.password == "admin"
    if not (correct_username and correct_password):
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.get("/docs", include_in_schema=False)
def get_docs(credentials: HTTPBasicCredentials = Depends(verify)):
    return get_swagger_ui_html(openapi_url="/openapi.json", title="MediGO Docs")

# === Run Locally ===
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
