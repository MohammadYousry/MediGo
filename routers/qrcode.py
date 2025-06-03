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
        qr_url = f"https://medigo-eg.netlify.app/{user_id}"  # ✅ الرابط الصحيح هنا
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
        qr_url = f"https://medigo-eg.netlify.app/{user_id}"  # ✅ نفس الرابط هنا

        qr_data_to_store = {
            "user_id": user_id,
            "last_accessed": now_timestamp,
            "expiration_date": expiration_date,
            "qr_image": saved_image_path,
            "qr_data": qr_url,
            "image_url": qr_url
        }

        get_qr_code_doc_ref(user_id).set(qr_data_to_store)

        return QRCodeResponse(**qr_data_to_store)
    except Exception as e:
        print(f"❌ [create_qr_code] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error creating QR code: {str(e)}")
