import firebase_admin
from firebase_admin import credentials, firestore, storage

# ✅ التحقق من أن Firebase لم يتم تهيئته مسبقًا
if not firebase_admin._apps:
    cred = credentials.Certificate("/etc/secrets/firebase_key.json")  # أو المسار الصحيح
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'medi-go-eb65e.appspot.com'
    })

# ✅ بعد التهيئة نقدر نستخدمهم بأمان
db = firestore.client()
bucket = storage.bucket()  # الآن يعمل بدون مشاكل
