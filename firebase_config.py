import firebase_admin
from firebase_admin import credentials, storage, firestore # أضفت firestore هنا احتياطًا لو بتحتاجوه

# Initialize Firebase Admin SDK with credentials
# عدّل السطر التالي ليشير إلى اسم ملف المفتاح الخاص بك مباشرة
cred = credentials.Certificate("/etc/secrets/firebase_key.json")

# Initialize the app only if it hasn't been initialized yet
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'medi-go-eb65e.firebasestorage.app'
    })


# Firestore client
db = firestore.client()

# You can get a reference to the bucket (optional, if you use storage)
# bucket = storage.bucket() # اسم الـ bucket هو نفسه اللي فوق بدون gs://

print("Firebase App initialized successfully with Firestore and Storage!")
