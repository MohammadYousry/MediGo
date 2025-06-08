from fastapi import APIRouter, HTTPException, Request
from models.schema import Allergy # Make sure the model is correct
from datetime import datetime
from firebase_config import db
from uuid import uuid4
import pytz

router = APIRouter(prefix="/allergies", tags=["Allergies"])
egypt_tz = pytz.timezone("Africa/Cairo")

@router.post("/{national_id}")
# The corrected line
def add_allergy(national_id: str, entry: AllergyCreate):
    user_ref = db.collection("Users").document(national_id)
    if not user_ref.get().exists:
        raise HTTPException(status_code=404, detail="User not found")

    record_id = str(uuid4())
    data = entry.dict()
    data["timestamp"] = datetime.now(egypt_tz).isoformat()
    data["id"] = record_id

    # ✅ Using the correct, simple path
    user_ref.collection("allergies").document(record_id).set(data)

    return {"message": "Allergy added", "id": record_id}

@router.get("/{national_id}")
def get_allergies(national_id: str):
    user_ref = db.collection("Users").document(national_id)
    if not user_ref.get().exists:
        raise HTTPException(status_code=404, detail="User not found")

    # ✅ Using the correct, simple path
    docs = user_ref.collection("allergies").stream()
    return [doc.to_dict() for doc in docs]

@router.put("/{national_id}/{record_id}")
def update_allergy(national_id: str, record_id: str, entry: Allergy):
    # ✅ Using the correct, simple path
    allergy_ref = db.collection("Users").document(national_id).collection("allergies").document(record_id)
    doc = allergy_ref.get()

    if not doc.exists:
        raise HTTPException(status_code=404, detail="Record not found")
    if doc.to_dict().get("added_by") != entry.added_by:
        raise HTTPException(status_code=403, detail="You are not authorized to update this record")

    updated_data = entry.dict()
    updated_data["timestamp"] = datetime.now(egypt_tz).isoformat()
    allergy_ref.update(updated_data)
    return {"message": "Allergy updated", "id": record_id}

@router.delete("/{national_id}/{record_id}")
def delete_allergy(national_id: str, record_id: str, request: Request):
    added_by = request.query_params.get("added_by")
    # ✅ Using the correct, simple path
    allergy_ref = db.collection("Users").document(national_id).collection("allergies").document(record_id)
    doc = allergy_ref.get()

    if not doc.exists:
        raise HTTPException(status_code=404, detail="Record not found")
    if doc.to_dict().get("added_by") != added_by:
        raise HTTPException(status_code=403, detail="You are not authorized to delete this record")

    allergy_ref.delete()
    return {"message": "Allergy deleted", "id": record_id}
