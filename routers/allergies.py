#
# routers/allergies.py - FINAL & CLEAN VERSION
#
from fastapi import APIRouter, HTTPException, Request
from models.schema import AllergyCreate, LegacyAllergy
from datetime import datetime
from firebase_config import db
from uuid import uuid4
import pytz

router = APIRouter(prefix="/allergies", tags=["Allergies"])
egypt_tz = pytz.timezone("Africa/Cairo")


# --- Your Original, Robust Endpoints ---

@router.post("/", response_model=dict)
def add_allergy(national_id: str, entry: AllergyCreate):
    user_ref = db.collection("Users").document(national_id)
    if not user_ref.get().exists:
        raise HTTPException(status_code=404, detail="User not found")

    record_id = str(uuid4())
    data = entry.dict()
    data["timestamp"] = datetime.now(egypt_tz).isoformat()
    data["id"] = record_id
    
    user_ref.collection("allergies").document(record_id).set(data)
    return {"message": "Allergy added", "id": record_id}

@router.get("/{national_id}", response_model=list)
def get_allergies(national_id: str):
    user_ref = db.collection("Users").document(national_id)
    if not user_ref.get().exists:
        raise HTTPException(status_code=404, detail="User not found")
    docs = user_ref.collection("allergies").stream()
    return [doc.to_dict() for doc in docs]

@router.put("/{national_id}/{record_id}", response_model=dict)
def update_allergy(national_id: str, record_id: str, entry: AllergyCreate):
    allergy_ref = db.collection("Users").document(national_id).collection("allergies").document(record_id)
    doc = allergy_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Record not found")

    if doc.to_dict().get("added_by") != entry.added_by:
        raise HTTPException(status_code=403, detail="You are not authorized to update this record")

    updated_data = entry.dict()
    allergy_ref.update(updated_data)
    return {"message": "Allergy updated", "id": record_id}

@router.delete("/{national_id}/{record_id}", response_model=dict)
def delete_allergy(national_id: str, record_id: str, request: Request):
    added_by = request.query_params.get("added_by")
    allergy_ref = db.collection("Users").document(national_id).collection("allergies").document(record_id)
    doc = allergy_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Record not found")

    if doc.to_dict().get("added_by") != added_by:
        raise HTTPException(status_code=403, detail="You are not authorized to delete this record")

    allergy_ref.delete()
    return {"message": "Allergy deleted", "id": record_id}


# --- ✅ Legacy Compatibility Endpoint (The Adapter) ---

@router.post("/legacy/{national_id}", tags=["Legacy Compatibility"])
def add_legacy_allergy(national_id: str, legacy_entry: LegacyAllergy):
    """
    Accepts Clara's old allergy model, translates it, and calls the new endpoint.
    """
    print("✅ Legacy allergy endpoint hit. Translating...")
    
    # --- Translation Stage ---
    new_data = {
        "allergen": legacy_entry.allergen_name,
        "reaction": legacy_entry.reaction_type,
        "severity": legacy_entry.severity,
        "notes": legacy_entry.notes,
        "added_by": legacy_entry.added_by or "patient" # Default if null
    }
    new_entry = AllergyCreate(**new_data)
    
    # --- Call Your Original, Robust Function ---
    return add_allergy(national_id, new_entry)
