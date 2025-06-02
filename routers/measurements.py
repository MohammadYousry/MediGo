from fastapi import APIRouter, HTTPException
from models.schema import HeightWeightCreate
from firebase_config import db
from datetime import datetime
import pytz

router = APIRouter(prefix="/measurements", tags=["Measurements"])
egypt_tz = pytz.timezone("Africa/Cairo")

@router.post("/body/{national_id}")
def add_height_weight(national_id: str, entry: HeightWeightCreate):
    height = entry.height
    weight = entry.weight

    if not height or not weight:
        raise HTTPException(status_code=400, detail="Height and weight are required")

    bmi = round(weight / ((height / 100) ** 2), 2)
    user_ref = db.collection("Users").document(national_id)

    if not user_ref.get().exists:
        raise HTTPException(status_code=404, detail="User not found")

    data = {
        "height": height,
        "weight": weight,
        "bmi": bmi,
        "date": datetime.now(egypt_tz).strftime("%Y-%m-%d %H:%M:%S")
    }

    user_ref.collection("ClinicalIndicators").document("measurements").set(data)
    return {"message": "Height, weight, and BMI saved", "bmi": bmi}

@router.get("/body/{national_id}")
def get_height_weight(national_id: str):
    doc = db.collection("Users").document(national_id).collection("ClinicalIndicators").document("measurements").get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Body measurements not found")
    return doc.to_dict()



# # === 2. General Measurement Records ===
# @router.post("/general/{national_id}")
# def add_measurement(national_id: str, entry: MeasurementRecordCreate):
#     user_ref = db.collection("Users").document(national_id)
#     added_by_name = "Unknown"

#     if entry.added_by == national_id:
#         # Patient → send to doctor
#         doctor_name = is_doctor_assigned(national_id)
#         assigned_to = doctor_name if doctor_name else "admin"

#         doc_ref = db.collection("PendingApprovals") \
#             .document(assigned_to) \
#             .collection("measurements") \
#             .document()

#         doc_ref.set({
#             "national_id": national_id,
#             "data_type": "measurements",
#             "record": entry.dict(),
#             "assigned_to": assigned_to,
#             "assigned_doctor_name": doctor_name,
#             "submitted_at": datetime.now(egypt_tz).isoformat()
#         })
#         return {"status": "submitted_for_approval", "assigned_to": assigned_to, "doc_id": doc_ref.id}

#     # Facility
#     facility_doc = db.collection("Facilities").document(entry.added_by).get()
#     if facility_doc.exists:
#         added_by_name = facility_doc.to_dict().get("facility_name", "Unknown")

#     # Direct Save
#     timestamp_id = datetime.now(egypt_tz).strftime("%Y-%m-%d %H:%M:%S")
#     data = entry.dict()
#     data["added_by_name"] = added_by_name
#     data["date"] = timestamp_id

#     user_ref.collection("measurements").document(timestamp_id).set(data)
#     return {"message": "Measurement added", "id": timestamp_id}


# @router.get("/general/{national_id}")
# def get_measurements(national_id: str):
#     docs = db.collection("Users").document(national_id).collection("measurements").stream()
#     return [doc.to_dict() | {"id": doc.id} for doc in docs if doc.id != "body"]
