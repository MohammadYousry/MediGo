from fastapi import APIRouter, HTTPException, Form
from datetime import datetime
import os
import qrcode
from firebase_admin import firestore
from firebase_config import db, bucket
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

        blob = bucket.blob(f"qr_codes/{user_id}_qrcode.png")
        blob.upload_from_filename(local_file_path)
        blob.make_public()

        os.remove(local_file_path)
        return blob.public_url

    except Exception as e:
        print(f"❌ [generate_qr_image] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"QR generation failed: {str(e)}")

# 🌐 إنشاء QR جديد
@router.post("/", response_model=QRCodeResponse)
async def create_qr_code(
    user_id: str = Form(...),
    expiration_date: str = Form(...)
):
    try:
        user_doc = db.collection("Users").document(user_id).get()
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="User does not exist")

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

# 🌐 استرجاع بيانات المستخدم لبطاقة الطوارئ
@router.get("/{user_id}", response_model=QRCodeWithUserInfoResponse)
def get_user_info_by_qr(user_id: str):
    user_doc = db.collection("Users").document(user_id).get()
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")

    user_data = user_doc.to_dict()

    # ✅ اجلب العمليات الجراحية
    user_data["surgeries"] = [
        doc.to_dict() for doc in db.collection("Users").document(user_id).collection("surgeries").stream()
    ]

    # ✅ اجلب التحاليل من مكانها الصحيح (داخل ClinicalIndicators)
    user_data["biomarkers"] = [
        doc.to_dict() for doc in db.collection("Users").document(user_id)
        .collection("ClinicalIndicators").document("bloodbiomarkers")
        .collection("Records").stream()
    ]

    # ✅ اجلب بيانات ضغط الدم (المرحلة)
    bp_docs = list(db.collection("Users").document(user_id)
        .collection("ClinicalIndicators").document("Hypertension")
        .collection("Records").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(1).stream())
    if bp_docs:
        latest_bp = bp_docs[0].to_dict()
        user_data["hypertension_stage"] = latest_bp.get("stage_name", "غير متوفر")

    # ✅ اجلب الأشعة
    user_data["radiology"] = [
        doc.to_dict() for doc in db.collection("Users").document(user_id).collection("radiology").stream()
    ]

    # ✅ اجلب الحساسية
    user_data["allergies"] = [
        doc.to_dict() for doc in db.collection("Users").document(user_id).collection("allergies").stream()
    ]

    # ✅ اجلب الأدوية
    user_data["medications"] = [
        doc.to_dict() for doc in db.collection("Users").document(user_id).collection("medications").stream()
    ]

    # ✅ اجلب الأمراض المزمنة من الحقل الرئيسي (قائمة)
    user_data["chronic_diseases"] = user_data.get("chronic_diseases", [])

    # ✅ اجلب جهات اتصال الطوارئ
    user_data["emergency_contacts"] = [
        doc.to_dict() for doc in db.collection("Users").document(user_id).collection("emergency_contacts").stream()
    ]

    return {
        "user_id": user_id,
        "user_info": user_data
    }
