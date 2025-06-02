from firebase_admin import credentials, firestore, initialize_app

# ✅ Initialize Firebase App (لو مش متعمل قبل كده)
try:
    initialize_app()
except:
    pass

db = firestore.client()

# ✅ المستخدمين اللي عايز تحدثلهم رابط QR (ممكن تحط أكتر من ID)
user_ids = [
    "12345678901235",
    "11111111111111",
    "30303030404040"
]

for national_id in user_ids:
    print(f"🔄 Updating QR for {national_id}...")
    qr_ref = db.collection("Users").document(national_id).collection("QRCodeAccess").document("single_qr_code")
    
    qr_ref.update({
        "image_url": f"https://medigo-eg.netlify.app/card/emergency_card.html?user_id={national_id}"
    })
    print(f"✅ Done for {national_id}")
