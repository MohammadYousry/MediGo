from datetime import datetime, date as dt_date
from fastapi import APIRouter, HTTPException, Request
from models.schema import MedicationEntry, MedicationCreate, LegacyMedicationEntry
from firebase_config import db
import pytz

egypt_tz = pytz.timezone("Africa/Cairo")
router = APIRouter(prefix="/medications", tags=["Medications"])

@router.post("/{national_id}")
def add_medication(national_id: str, entry: MedicationCreate):
    user_ref = db.collection("Users").document(national_id)
    if not user_ref.get().exists:
        raise HTTPException(status_code=404, detail="User not found")

    if entry.current and not entry.start_date:
        raise HTTPException(
            status_code=400,
            detail="Start date must be provided for currently taken medications."
        )

    medication_data = entry.dict()
    timestamp_id = datetime.now(egypt_tz).strftime("%Y-%m-%d %H:%M:%S")

    # This date conversion logic is still useful
    if isinstance(entry.start_date, dt_date):
        medication_data["start_date"] = entry.start_date.isoformat()
    if isinstance(entry.end_date, dt_date):
        medication_data["end_date"] = entry.end_date.isoformat()

    # ❌ The problematic block of code has been REMOVED from here.
    
    medication_data["timestamp"] = timestamp_id
    # Let's use the timestamp as the ID for medications as well for consistency
    medication_data["id"] = timestamp_id

    user_ref.collection("medications").document(timestamp_id).set(medication_data)
    return {"message": "Medication added", "doc_id": timestamp_id}


@router.get("/{national_id}")
def get_medications(national_id: str):
    user_ref = db.collection("Users").document(national_id)
    if not user_ref.get().exists:
        raise HTTPException(status_code=404, detail="User not found")

    docs = user_ref.collection("medications").stream()
    return [{"doc_id": doc.id, **doc.to_dict()} for doc in docs]


@router.put("/{national_id}/{record_id}")
def update_medication(national_id: str, record_id: str, entry: MedicationCreate):
    med_ref = db.collection("Users").document(national_id).collection("medications").document(record_id)
    doc = med_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Record not found")

    if doc.to_dict().get("added_by") != entry.added_by:
        raise HTTPException(status_code=403, detail="You are not authorized to update this record")

    if entry.current and not entry.start_date:
        raise HTTPException(
            status_code=400,
            detail="Start date must be provided for currently taken medications."
        )

    updated_data = entry.dict()

    if isinstance(entry.start_date, dt_date):
        updated_data["start_date"] = entry.start_date.isoformat()
    if isinstance(entry.end_date, dt_date):
        updated_data["end_date"] = entry.end_date.isoformat()
    
    # ❌ The problematic block of code has been REMOVED from here as well.
    
    # Use update() instead of set() for partial updates
    med_ref.update(updated_data)

    return {"message": "Medication updated", "id": record_id}


@router.delete("/{national_id}/{record_id}")
def delete_medication(national_id: str, record_id: str, request: Request):
    added_by = request.query_params.get("added_by")
    med_ref = db.collection("Users").document(national_id).collection("medications").document(record_id)
    doc = med_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Record not found")

    if doc.to_dict().get("added_by") != added_by:
        raise HTTPException(status_code=403, detail="You are not authorized to delete this record")

    med_ref.delete()
    return {"message": "Medication deleted", "id": record_id}

# في routers/medications.py

# ... دوالك الحالية تبقى كما هي

@router.post("/legacy/medications/{national_id}", tags=["Legacy Compatibility"])
def add_legacy_medication(national_id: str, legacy_entry: LegacyMedicationEntry):
    print(f"✅ Legacy medication endpoint hit for user {national_id}.")
    
    # --- 1. الترجمة ---
    new_med_data = {
        "name": legacy_entry.trade_name,  # ترجمة trade_name إلى name
        "dosage": legacy_entry.dosage,
        "frequency": legacy_entry.frequency,
        "start_date": legacy_entry.start_date.isoformat() if legacy_entry.start_date else None,
        "end_date": legacy_entry.end_date.isoformat() if legacy_entry.end_date else None,
        "current": legacy_entry.current,
        "reason": legacy_entry.notes,
        "added_by": legacy_entry.added_by
    }
    new_entry = MedicationCreate(**new_med_data)
    
    # --- 2. استدعاء الدالة الأصلية ---
    print("✅ Translation complete. Calling the main add_medication function.")
    return add_medication(national_id, new_entry)
