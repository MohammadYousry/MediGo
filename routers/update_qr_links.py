from firebase_admin import credentials, firestore, initialize_app

# ✅ Initialize Firebase Admin SDK (if not already initialized)
try:
    initialize_app()
except:
    pass

# ✅ Firestore client
db = firestore.client()

# ✅ Loop through all users in the "Users" collection
users_ref = db.collection("Users").stream()

for doc in users_ref:
    national_id = doc.id
    print(f"🔄 Updating QR for {national_id}...")

    qr_ref = db.collection("Users").document(national_id).collection("QRCodeAccess").document("single_qr_code")

    # ✅ Set the correct public-facing link (Netlify)
    qr_ref.set({
        "image_url": f"https://medigo-eg.netlify.app/card/emergency_card.html?user_id={national_id}"
    }, merge=True)

    print(f"✅ Done for {national_id}")

print("🎉 All QR links updated successfully.")
