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

@router.get("/{user_id}", response_model=QRCodeWithUserInfoResponse)
def get_user_info_by_qr(user_id: str):
    user_doc = db.collection("Users").document(user_id).get()
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")

    user_data = user_doc.to_dict()

    def get_collection_fallback(primary_path, fallback_field):
        try:
            data = [doc.to_dict() for doc in primary_path.stream()]
            if data:
                return data
        except:
            pass
        return user_data.get(fallback_field, [])

    # ✅ العمليات الجراحية
    user_data["surgeries"] = get_collection_fallback(
        db.collection("Users").document(user_id).collection("surgeries"), "surgeries"
    )

    # ✅ الأشعة
    user_data["radiology"] = get_collection_fallback(
        db.collection("Users").document(user_id)
        .collection("ClinicalIndicators")
        .document("radiology")
        .collection("Records"), "radiology"
    )

    # ✅ التحاليل
    user_data["biomarkers"] = get_collection_fallback(
        db.collection("Users").document(user_id)
        .collection("ClinicalIndicators")
        .document("bloodbiomarkers")
        .collection("Records"), "biomarkers"
    )

    # ✅ ضغط الدم
    bp_docs = list(db.collection("Users").document(user_id)
        .collection("ClinicalIndicators")
        .document("Hypertension")
        .collection("Records")
        .order_by("timestamp", direction=firestore.Query.DESCENDING)
        .limit(1)
        .stream())

    user_data["hypertension_stage"] = None
    if bp_docs:
        latest_bp = bp_docs[0].to_dict()
        systolic = latest_bp.get("systolic")
        diastolic = latest_bp.get("diastolic")

        def classify_bp_stage(sys, dia):
            if sys >= 180 or dia >= 120:
                return "Stage 3 - Hypertensive Crisis"
            elif sys >= 140 or dia >= 90:
                return "Stage 2 - Hypertension"
            elif sys >= 130 or dia >= 80:
                return "Stage 1 - Hypertension"
            elif sys >= 120 and dia < 80:
                return "Elevated"
            else:
                return "Normal"

        if systolic is not None and diastolic is not None:
            user_data["hypertension_stage"] = classify_bp_stage(systolic, diastolic)
        else:
            user_data["hypertension_stage"] = "غير متوفر"

    # ✅ الحساسية
    user_data["allergies"] = get_collection_fallback(
        db.collection("Users").document(user_id).collection("allergies"), "allergies"
    )

    # ✅ الأدوية
    user_data["medications"] = get_collection_fallback(
        db.collection("Users").document(user_id).collection("medications"), "medications"
    )

    # ✅ الأمراض المزمنة
    user_data["chronic_diseases"] = user_data.get("chronic_diseases", [])

    # ✅ جهات الطوارئ
    user_data["emergency_contacts"] = get_collection_fallback(
        db.collection("Users").document(user_id).collection("emergency_contacts"), "emergency_contacts"
    )
    # In routers/qrcode.py, inside get_user_info_by_qr

    # ... (after fetching emergency_contacts)

    # --- ADD THESE TWO BLOCKS ---

    # ✅ التشخيصات
    user_data["diagnoses"] = get_collection_fallback(
        db.collection("Users").document(user_id).collection("diagnoses"), "diagnoses"
    )

    # ✅ التاريخ العائلي
    user_data["family_history"] = get_collection_fallback(
        db.collection("Users").document(user_id).collection("family_history"), "family_history"
    )
    
    # ... (before profile_photo logic)
    # In routers/qrcode.py at the end of the get_user_info_by_qr function

    # ... (all the data fetching logic remains the same)

    # ✅ صورة البروفايل (Refined Logic)
    # This ensures we get a valid URL or the default one.
    user_data["profile_photo"] = (
        user_data.get("profile_picture_url") or
        user_data.get("profile_photo") or
        user_data.get("profile_image") or
        "https://medigo-eg.netlify.app/medi_go_logo.png"  # Fallback
    )
    
    # The final returned object should be structured to match QRCodeWithUserInfoResponse
    # The key is to pass the user_data dictionary directly to the user_info field.
    return QRCodeWithUserInfoResponse(
        user_id=user_id,
        user_info=user_data 
    )



