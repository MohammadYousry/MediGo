from fastapi import APIRouter, HTTPException
from firebase_config import db
from models.schema import UserCreate, UserUpdate, UserResponse, calculate_age
from datetime import datetime
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
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid birthdate format. Use YYYY-MM-DD.")

    user_data = {**user.dict(), "age": age}
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

# -------------------- Update User --------------------
@router.put("/{national_id}", response_model=dict)
async def update_user(national_id: str, updated_user: UserUpdate):
    user_ref = get_user_ref(national_id)
    existing_user = user_ref.get()
    if not existing_user.exists:
        raise HTTPException(status_code=404, detail="User not found")

    updates = updated_user.dict(exclude_unset=True)

    if "date_of_birth" in updates:
        try:
            birthday_date = datetime.strptime(updates["date_of_birth"], "%Y-%m-%d")
            age = (datetime.now().date() - birthday_date.date()).days // 365
            updates["age"] = age
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
    return user_doc.to_dict()

# -------------------- Get Users List --------------------
@router.get("/", response_model=List[UserResponse])
def get_users(name: str = "", national_id: str = ""):
    users_ref = db.collection("Users")
    results = []

    for doc in users_ref.stream():
        user = doc.to_dict()
        user["id"] = doc.id

        if (
            name.lower() in user.get("full_name", "").lower()
            or national_id.lower() in user.get("national_id", "").lower()
            or national_id.lower() in user.get("doctoremail", "").lower()
        ):
            results.append(user)

    return results
