from fastapi import APIRouter, HTTPException, File, Form, UploadFile
from fastapi.responses import FileResponse
import os
import shutil
from firebase_config import db
from datetime import datetime

# عدّل الـ imports لتناسب الموديلات الجديدة/المعدلة في schema.py
from models.schema import (
    QRCodeCreate, # افترضت أنك قد تحتاجه لـ POST لكن create_qr_code الحالي لا يستخدمه كـ body
    QRCodeResponse, # يمثل ما يتم تخزينه في Firestore للـ QR
    QRCodeWithUserInfoResponse,
    UserEmergencyInfo,
    calculate_age # استيراد دالة حساب العمر
)

router = APIRouter(prefix="/qrcode", tags=["QR Codes"])

def get_qr_code_doc_ref(user_id: str):
    return db.collection("Users").document(user_id).collection("QRCodeAccess").document("single_qr_code")

async def save_uploaded_image(user_id: str, file: UploadFile) -> str:
    try:
        folder = f"./qr_images/{user_id}"
        os.makedirs(folder, exist_ok=True)
        file_name = f"{user_id}_qrcode.png" # أو اسم فريد أكثر لو أردت
        file_path = os.path.join(folder, file_name)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        # Consider returning a URL accessible by the client, not a local file path
        # For now, local path as per original code for qr_image storage
        return f"./qr_images/{user_id}/{file_name}".replace("\\", "/") # Ensure forward slashes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save image: {str(e)}")

@router.post("/", response_model=QRCodeResponse) # Note: response_model is QRCodeResponse here
async def create_qr_code(
    user_id: str = Form(...),
    # last_accessed: str = Form(...), # This will be set to now
    expiration_date: str = Form(...), # Expecting YYYY-MM-DDTHH:MM:SS or similar
    qr_image: UploadFile = File(...)
):
    try:
        saved_image_path = await save_uploaded_image(user_id, qr_image)
        now_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        qr_data_to_store = {
            "user_id": user_id,
            "last_accessed": now_timestamp,
            "expiration_date": expiration_date,
            "qr_image": saved_image_path, # This is a local server path
            "qr_data": f"{user_id}|{now_timestamp}" # Example data to encode in actual QR
        }

        doc_ref = get_qr_code_doc_ref(user_id)
        print(f"[DEBUG][create_qr_code] Saving QR data to Firestore at: {doc_ref.path} with data: {qr_data_to_store}")
        doc_ref.set(qr_data_to_store)
        print("[DEBUG][create_qr_code] Firestore save successful")

        return QRCodeResponse(**qr_data_to_store) # Return the stored data
    except Exception as e:
        print(f"❌ [create_qr_code] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error creating QR code: {str(e)}")


@router.get("/{user_id}", response_model=QRCodeWithUserInfoResponse)
async def get_qr_code(user_id: str):
    try:
        # 1. Get QR Code specific data from subcollection
        qr_doc_ref = get_qr_code_doc_ref(user_id)
        qr_doc = qr_doc_ref.get()

        if not qr_doc.exists:
            print(f"[get_qr_code] QR Code document not found for user_id: {user_id} at path: {qr_doc_ref.path}")
            raise HTTPException(status_code=404, detail="QR Code data not found for this user in QRCodeAccess.")
        
        qr_specific_data = qr_doc.to_dict()
        print(f"[get_qr_code] Successfully fetched QR specific data: {qr_specific_data}")

        # 2. Get User's main data from 'Users' collection
        user_doc_ref = db.collection("Users").document(user_id)
        user_doc = user_doc_ref.get()
        user_emergency_info_data = None

        if user_doc.exists:
            user_main_data = user_doc.to_dict()
            print(f"[get_qr_code] Successfully fetched main user data for {user_id}: {user_main_data}")
            
            # Calculate age using the imported function
            calculated_age = calculate_age(user_main_data.get("date_of_birth"))

            user_emergency_info_data = UserEmergencyInfo(
                full_name=user_main_data.get("full_name"),
                national_id=user_main_data.get("national_id", user_id), # Fallback to user_id if national_id not in user_doc
                gender=user_main_data.get("gender"),
                date_of_birth=user_main_data.get("date_of_birth"),
                phone_number=user_main_data.get("phone_number"),
                address=user_main_data.get("address"),
                city=user_main_data.get("city"),
                region=user_main_data.get("region"),
                blood_type=user_main_data.get("blood_type") or user_main_data.get("blood_group"),
                profile_picture_url=user_main_data.get("profile_picture_url") or user_main_data.get("profile_photo"),
                age=calculated_age, # Use the calculated age
                emergency_contacts=user_main_data.get("emergency_contacts", []),
                allergies=user_main_data.get("allergies", []),
                chronic_diseases=user_main_data.get("chronic_diseases", []),
                medications=user_main_data.get("medications", [])
            )
        else:
            print(f"[get_qr_code] Main user document not found for user_id: {user_id} at path: {user_doc_ref.path}")
            # If user_info is critical, you might raise an error here or return user_info as None / empty

        # 3. Combine and return
        final_response = QRCodeWithUserInfoResponse(
            user_id=qr_specific_data.get("user_id", user_id),
            last_accessed=qr_specific_data.get("last_accessed"),
            expiration_date=qr_specific_data.get("expiration_date"),
            qr_image=qr_specific_data.get("qr_image"), # This is still the local server path
            user_info=user_emergency_info_data
        )
        
        print(f"[get_qr_code] Final combined response for user_id {user_id} will be (showing user_info part): {user_emergency_info_data.model_dump_json(indent=2) if user_emergency_info_data else 'No user_info'}")
        return final_response

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"❌ [get_qr_code] Unexpected error for user_id {user_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@router.get("/images/{user_id}/{file_name}", response_class=FileResponse)
async def serve_image(user_id: str, file_name: str):
    try:
        # Construct path relative to the project root or a defined static files directory
        # The "./qr_images/" implies it's relative to where the script is run.
        image_file_path = os.path.join("qr_images", user_id, file_name)
        print(f"[serve_image] Attempting to serve image from: {os.path.abspath(image_file_path)}")

        if not os.path.exists(image_file_path):
            print(f"❌ [serve_image] Image not found at: {image_file_path}")
            raise HTTPException(status_code=404, detail="Image not found")

        return FileResponse(image_file_path, media_type="image/png")
    except Exception as e:
        print(f"❌ [serve_image] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error serving image: {str(e)}")