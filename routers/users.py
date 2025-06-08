from fastapi import APIRouter, HTTPException
from firebase_config import db
from models.schema import UserCreate, LegacyUserCreate, UserUpdate, UserResponse, calculate_age


from datetime import datetime, date
from typing import List

router = APIRouter(prefix="/users", tags=["Users"])

# -------------------- Helper --------------------
def get_user_ref(national_id: str):
    return db.collection("Users").document(national_id)

# -------------------- Create User --------------------
@router.post("/", response_model=UserResponse)
def create_user(user: UserCreate):
    user_ref = get_user_ref(user.national_id)
    if user_ref.get().exists:
        raise HTTPException(status_code=400, detail="User already exists")

    try:
        age = calculate_age(user.date_of_birth)
        if age is None or age < 0 or age > 130:
            raise ValueError("Age out of bounds.")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid birthdate format. Use YYYY-MM-DD.")

    user_data = {**user.dict(), "age": age}
    user_data["date_of_birth"] = str(user.date_of_birth)

    user_ref.set(user_data)

    # ✅ Doctor check and admin notification
    if user.doctoremail:
        doctor_query = db.collection("Doctors").where("email", "==", user.doctoremail).limit(1).stream()
        doctor_doc = next(doctor_query, None)

        if not doctor_doc:
            notif_id = f"{user.doctoremail}_{user.national_id}"
            db.collection("AdminNotifications").document("unregistered_doctors") \
              .collection("Notifications").document(notif_id).set({
                  "patient_national_id": user.national_id,
                  "doctor_email": user.doctoremail,
                  "message": f"⚠️ Patient {user.full_name} ({user.national_id}) assigned to unregistered doctor: {user.doctoremail}",
                  "timestamp": datetime.now().isoformat()
              })

    print(f"✅ Created user {user.full_name} ({user.national_id})")
    return {**user.dict(), "age": age}

# ✅ Legacy Compatibility Endpoint
@router.post("/legacy/", tags=["Legacy Compatibility"], response_model=UserResponse)
def create_legacy_user(legacy_user: LegacyUserCreate):
    """Accepts the OLD user structure, translates it, and calls the new create_user function."""
    print("✅ Legacy user endpoint hit. Translating to new format...")
    
    new_user_data = {
        "national_id": legacy_user.national_id,
        "password": legacy_user.password,
        "full_name": legacy_user.full_name,
        "date_of_birth": legacy_user.birthdate, # Translation
        "phone_number": legacy_user.phone_number,
        "email": legacy_user.email,
        "gender": legacy_user.gender,
        "blood_type": legacy_user.blood_group, # Translation
        "address": legacy_user.address,
        "region": legacy_user.region,
        "city": legacy_user.city,
        "profile_picture_url": legacy_user.profile_photo,
        "current_smoker": legacy_user.current_smoker,
        "cigs_per_day": legacy_user.cigs_per_day,
        "doctoremail": None # Clara's model doesn't have this
    }
    
    new_user_object = UserCreate(**new_user_data)
    
    print("✅ Translation complete. Calling the main create_user function.")
    return create_user(new_user_object)
    
# -------------------- Update User --------------------
@router.put("/{national_id}", response_model=dict)
async def update_user(national_id: str, updated_user: UserUpdate):
    user_ref = get_user_ref(national_id)
    existing_user = user_ref.get()
    if not existing_user.exists:
        raise HTTPException(status_code=404, detail="User not found")

    updates = updated_user.dict(exclude_unset=True)

    # ✅ دعم الاسم القديم للحقل (لو موجود)
    if "birthdate" in updates and "date_of_birth" not in updates:
        updates["date_of_birth"] = updates.pop("birthdate")

    if "date_of_birth" in updates:
        try:
            birth = updates["date_of_birth"]
            birth_date = birth if isinstance(birth, date) else datetime.strptime(birth, "%Y-%m-%d").date()
            age = (datetime.now().date() - birth_date).days // 365
            if age < 0 or age > 130:
                raise ValueError("Unrealistic age")
            updates["age"] = age
            updates["date_of_birth"] = str(birth_date)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid birthdate format. Use YYYY-MM-DD.")

    user_ref.update(updates)
    print(f"🔄 Updated user {national_id}")
    return {"message": "User updated successfully"}

# -------------------- Get Single User --------------------
@router.get("/{national_id}", response_model=UserResponse)
def get_user(national_id: str):
    user_doc = get_user_ref(national_id).get()
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")
    
    data = user_doc.to_dict()
    data["user_id"] = national_id
    return data

# -------------------- Get Users List --------------------
@router.get("/", response_model=List[UserResponse])
def get_users(name: str = "", national_id: str = ""):
    users_ref = db.collection("Users")
    results = []

    for doc in users_ref.stream():
        user = doc.to_dict()
        user["user_id"] = doc.id

        if (
            name.lower() in user.get("full_name", "").lower()
            or national_id.lower() in user.get("national_id", "").lower()
            or national_id.lower() in user.get("doctoremail", "").lower()
        ):
            results.append(user)

    return results

# ✅ هذا هو الـ Endpoint الجديد الذي يعمل كمترجم
@router.post("/legacy/users/", tags=["Legacy Compatibility"], response_model=UserResponse)
def create_legacy_user(legacy_user: LegacyUserCreate):
    """
    This endpoint accepts the OLD user structure from Clara's app,
    translates it, and then calls our new, robust create_user function.
    """
    print("✅ Legacy user endpoint hit. Translating to new format...")

    # --- 1. مرحلة الترجمة ---
    # نقوم بتحويل البيانات من نموذج كلارا القديم إلى نموذجنا الجديد
    new_user_data = {
        "national_id": legacy_user.national_id,
        "password": legacy_user.password,
        "full_name": legacy_user.full_name,
        "date_of_birth": legacy_user.birthdate,  # <-- لاحظ الفرق في الاسم
        "phone_number": legacy_user.phone_number,
        "email": legacy_user.email,
        "gender": legacy_user.gender,
        "blood_type": legacy_user.blood_group, # <-- لاحظ الفرق في الاسم
        "address": legacy_user.address,
        "region": legacy_user.region,
        "city": legacy_user.city,
        "profile_picture_url": legacy_user.profile_photo,
        "current_smoker": legacy_user.current_smoker,
        "cigs_per_day": legacy_user.cigs_per_day,
    }

    # نقوم بإنشاء كائن من نموذجنا الصحيح
    new_user_object = UserCreate(**new_user_data)

    # --- 2. استدعاء الدالة الأصلية ---
    # الآن نستدعي دالة create_user السليمة التي لدينا بالفعل
    print("✅ Translation complete. Calling the main create_user function.")
    return create_user(new_user_object)
