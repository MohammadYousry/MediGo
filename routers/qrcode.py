# qrcode.py

from fastapi import APIRouter, HTTPException, Form
from datetime import datetime
import os
import qrcode

from firebase_config import db, bucket  # ✅ استخدام التهيئة الموحدة
from models.schema import (
    QRCodeResponse,
    QRCodeWithUserInfoResponse,
    UserEmergencyInfo
)

router = APIRouter(prefix="/qrcode", tags=["QR Codes"])

# 📁 مرجع Firestore لمستند QR
def get_qr_code_doc_ref(user_id: str):
    return db.collection("Users").document(user_id).collection("QRCodeAccess").document("single_qr_code")

# 🧠 توليد صورة QR ورفعها إلى Firebase Storage
def generate_qr_image(user_id: str) -> str:
    try:
        qr_url = f"https://medigo-eg.netlify.app/card/emergency_card.html?user_id={user_id}"
        local_folder = f"./qr_images/{user_id}"
        os.makedirs(local_folder, exist_ok=True)
        local_file_path = os.path.join(local_folder, f"{user_id}_qrcode.png")

        # ✅ توليد صورة QR
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4
        )
        qr.add_data(qr_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(local_file_path)

        # ✅ رفع الصورة إلى Firebase
        blob = bucket.blob(f"qr_codes/{user_id}_qrcode.png")
        blob.upload_from_filename(local_file_path)
        blob.make_public()

        os.remove(local_file_path)  # 🧹 تنظيف
        return blob.public_url

    except Exception as e:
        print(f"❌ [generate_qr_image] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"QR generation failed: {str(e)}")

# 🌐 API - إنشاء QR Code وتخزينه في Firestore
@router.post("/", response_model=QRCodeResponse)
async def create_qr_code(
    user_id: str = Form(...),
    expiration_date: str = Form(...)
):
    try:
        # ✅ تحقق من أن المستخدم موجود قبل توليد QR
        user_doc = db.collection("Users").document(user_id).get()
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="User does not exist")

        # 🧠 توليد QR ورفعه
        image_url = generate_qr_image(user_id)
        now_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        web_url = f"https://medigo-eg.netlify.app/card/emergency_card.html?user_id={user_id}"

        qr_data_to_store = {
            "user_id": user_id,
            "last_accessed": now_timestamp,
            "expiration_date": expiration_date,
            "qr_image": image_url,
            "qr_data": web_url,
            "image_url": image_url
        }

        get_qr_code_doc_ref(user_id).set(qr_data_to_store)
        return QRCodeResponse(**qr_data_to_store)

    except Exception as e:
        print(f"❌ [create_qr_code] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating QR code: {str(e)}")

# 🌐 API - استرجاع بيانات المستخدم لصفحة emergency_card
@router.get("/{user_id}", response_model=QRCodeWithUserInfoResponse)
def get_user_info_by_qr(user_id: str):
    user_doc = db.collection("Users").document(user_id).get()
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")

    user_info = user_doc.to_dict()
    return {
        "user_id": user_id,
        "user_info": user_info
    }
