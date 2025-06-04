import firebase_admin
from firebase_admin import credentials, firestore, storage

cred = credentials.Certificate("/etc/secrets/firebase_key.json")  # أو المسار الصحيح عندك

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'medi-go-eb65e.appspot.com'  # ✅ الاسم الصحيح
    })

db = firestore.client()
