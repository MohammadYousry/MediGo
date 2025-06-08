from fastapi import APIRouter, HTTPException, Request
from models.schema import EmergencyContactCreate, LegacyEmergencyContact
from firebase_config import db
from datetime import datetime
import pytz

router = APIRouter(prefix="/emergency-contacts", tags=["Emergency Contacts"])
egypt_tz = pytz.timezone("Africa/Cairo")

# ---------------------- Add Emergency Contact ----------------------
@router.post("/{national_id}")
def add_contact(national_id: str, entry: EmergencyContactCreate):
    user_ref = db.collection("Users").document(national_id)
    if not user_ref.get().exists:
        raise HTTPException(status_code=404, detail="User not found")

    record_id = datetime.now(egypt_tz).strftime("%Y-%m-%d %H:%M:%S")
    data = entry.dict()
    data["id"] = record_id
    data["user_id"] = national_id
    data["timestamp"] = record_id

    user_ref.collection("emergency_contacts").document(record_id).set(data)
    return {"message": "Emergency contact added", "record_id": record_id}

# --- ✅ Legacy Compatibility Endpoint (The Adapter) ---

@router.post("/legacy/{national_id}", tags=["Legacy Compatibility"])
def add_legacy_contact(national_id: str, legacy_entry: LegacyEmergencyContact):
    """Accepts Clara's old emergency contact model and translates it."""
    print("✅ Legacy emergency contact endpoint hit. Translating...")
    
    # --- Translation Stage ---
    new_data = {
        "name": legacy_entry.full_name,
        "relationship": legacy_entry.relationship,
        "phone_number": legacy_entry.phone_number,
        "added_by": "patient" # Clara's model doesn't have this, so we add a default
    }
    new_entry = EmergencyContactCreate(**new_data)
    
    # --- Call Your Original, Robust Function ---
    return add_contact(national_id, new_entry)

# ---------------------- Get All Emergency Contacts ----------------------
@router.get("/{national_id}")
def get_contacts(national_id: str):
    user_ref = db.collection("Users").document(national_id)
    if not user_ref.get().exists:
        raise HTTPException(status_code=404, detail="User not found")

    docs = user_ref.collection("emergency_contacts").stream()
    return [doc.to_dict() for doc in docs]

# ---------------------- Update Emergency Contact ----------------------
@router.put("/{national_id}/{record_id}")
def update_contact(national_id: str, record_id: str, entry: EmergencyContactCreate):
    record_ref = db.collection("Users").document(national_id) \
        .collection("emergency_contacts").document(record_id)

    existing_doc = record_ref.get()
    if not existing_doc.exists:
        raise HTTPException(status_code=404, detail="Record not found")

    # 🔐 Check if added_by matches
    if existing_doc.to_dict().get("added_by") != entry.added_by:
        raise HTTPException(status_code=403, detail="You are not authorized to update this contact.")

    data = entry.dict()
    data["id"] = record_id
    data["user_id"] = national_id
    data["timestamp"] = record_id

    record_ref.set(data)
    return {"message": "Emergency contact updated", "record_id": record_id}

# ---------------------- Delete Emergency Contact ----------------------
@router.delete("/{national_id}/{record_id}")
def delete_contact(national_id: str, record_id: str, request: Request):
    added_by = request.query_params.get("added_by")

    record_ref = db.collection("Users").document(national_id) \
        .collection("emergency_contacts").document(record_id)

    doc = record_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Record not found")

    # 🔐 Validate ownership
    if doc.to_dict().get("added_by") != added_by:
        raise HTTPException(status_code=403, detail="You are not authorized to delete this contact.")

    record_ref.delete()
    return {"message": "Emergency contact deleted", "record_id": record_id}
