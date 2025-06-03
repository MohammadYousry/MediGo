from fastapi import APIRouter, HTTPException, Form
from fastapi.responses import FileResponse
import os
from firebase_config import db
from datetime import datetime
import qrcode

from models.schema import (
    QRCodeResponse,
    QRCodeWithUserInfoResponse,
    UserEmergencyInfo,
    calculate_age
)

router = APIRouter(prefix="/qrcode", tags=["QR Codes"])

def get_qr_code_doc_ref(user_id: str):
    return db.collection("Users").document(user_id).collection("QRCodeAccess").document("single_qr_code")

def generate_qr_image(user_id: str) -> str:
    try:
        qr_url = f"https:/https://medigo-eg.netlify.app//{user_id}"
        folder = f"./qr_images/{user_id}"
        os.makedirs(folder, exist_ok=True)
        file_path = os.path.join(folder, f"{user_id}_qrcode.png")

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4
        )
        qr.add_data(qr_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img.save(file_path)

        return file_path.replace("\\", "/")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"QR generation failed: {str(e)}")

@router.post("/", response_model=QRCodeResponse)
async def create_qr_code(
    user_id: str = Form(...),
    expiration_date: str = Form(...)
):
    try:
        saved_image_path = generate_qr_image(user_id)
        now_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        image_url = f"https://medigo.site/{user_id}"

        qr_data_to_store = {
            "user_id": user_id,
            "last_accessed": now_timestamp,
            "expiration_date": expiration_date,
            "qr_image": saved_image_path,
            "qr_data": image_url,
            "image_url": image_url
        }

        doc_ref = get_qr_code_doc_ref(user_id)
        doc_ref.set(qr_data_to_store)

        return QRCodeResponse(**qr_data_to_store)
    except Exception as e:
        print(f"❌ [create_qr_code] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error creating QR code: {str(e)}")

async def fetch_subcollection_data(user_id: str, subcollection: str):
    try:
        docs = db.collection("Users").document(user_id).collection(subcollection).stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        print(f"Error fetching {subcollection}: {e}")
        return []

@router.get("/{user_id}", response_model=QRCodeWithUserInfoResponse)
async def get_qr_code(user_id: str):
    try:
        qr_doc_ref = get_qr_code_doc_ref(user_id)
        qr_doc = qr_doc_ref.get()

        if not qr_doc.exists:
            raise HTTPException(status_code=404, detail="QR Code data not found for this user in QRCodeAccess.")

        qr_specific_data = qr_doc.to_dict()
        user_doc_ref = db.collection("Users").document(user_id)
        user_doc = user_doc_ref.get()

        user_emergency_info_data = None
        if user_doc.exists:
            user_main_data = user_doc.to_dict()
            calculated_age = calculate_age(user_main_data.get("birthdate"))

            # Fetch subcollections
            allergies = await fetch_subcollection_data(user_id, "allergies")
            medications = await fetch_subcollection_data(user_id, "medications")
            diagnoses = await fetch_subcollection_data(user_id, "diagnoses")
            chronic_diseases = [entry.get("diagnosis_name", "غير محدد") for entry in diagnoses]
            surgeries = await fetch_subcollection_data(user_id, "surgeries")
            radiology = await fetch_subcollection_data(user_id, "radiology")
            bloodbiomarkers = await fetch_subcollection_data(user_id, "bloodbiomarkers")
            emergency_contacts = await fetch_subcollection_data(user_id, "emergency_contacts")

            hypertension_ref = user_doc_ref.collection("ClinicalIndicators").document("Hypertension")
            hypertension_doc = hypertension_ref.get()
            hypertension_stage = hypertension_doc.to_dict().get("hypertension_stage", "غير متوفر") if hypertension_doc.exists else "غير متوفر"

            user_emergency_info_data = UserEmergencyInfo(
                full_name=user_main_data.get("full_name"),
                national_id=user_main_data.get("national_id", user_id),
                gender=user_main_data.get("gender"),
                birthdate=user_main_data.get("birthdate"),
                phone_number=user_main_data.get("phone_number"),
                address=user_main_data.get("address"),
                city=user_main_data.get("city"),
                region=user_main_data.get("region"),
                blood_type=user_main_data.get("blood_type") or user_main_data.get("blood_group"),
                profile_picture_url=user_main_data.get("profile_picture_url") or user_main_data.get("profile_photo"),
                age=calculated_age,
                emergency_contacts=emergency_contacts,
                allergies=allergies,
                chronic_diseases=chronic_diseases,
                medications=medications,
                surgeries=surgeries,
                radiology=radiology,
                bloodbiomarkers=bloodbiomarkers,
                hypertension_stage=hypertension_stage
            )

        return QRCodeWithUserInfoResponse(
            user_id=qr_specific_data.get("user_id", user_id),
            last_accessed=qr_specific_data.get("last_accessed"),
            expiration_date=qr_specific_data.get("expiration_date"),
            qr_image=qr_specific_data.get("qr_image"),
            image_url=qr_specific_data.get("image_url"),
            user_info=user_emergency_info_data
        )

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"❌ [get_qr_code] Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.get("/images/{user_id}/{file_name}", response_class=FileResponse)
async def serve_image(user_id: str, file_name: str):
    try:
        image_file_path = os.path.join("qr_images", user_id, file_name)
        if not os.path.exists(image_file_path):
            raise HTTPException(status_code=404, detail="Image not found")
        return FileResponse(image_file_path, media_type="image/png")
    except Exception as e:
        print(f"❌ [serve_image] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error serving image: {str(e)}")
