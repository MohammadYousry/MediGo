import firebase_admin
from firebase_admin import credentials, storage, firestore

cred = credentials.Certificate("/etc/secrets/firebase_key.json")

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'medi-go-eb65e.appspot.com'  # ✅ ده الصح
    })

db = firestore.client()

print("Firebase App initialized successfully with Firestore and Storage!")
