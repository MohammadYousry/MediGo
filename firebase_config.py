from firebase_admin import storage, firestore

import firebase_admin
from firebase_admin import credentials, storage

# Initialize Firebase Admin SDK with credentials
cred = credentials.Certificate(r"C:\Users\CLARA\Downloads\Final Graduation Project\Final Graduation Project\medi-go-eb65e-firebase-adminsdk-fbsvc-0f0bae21e5.json")

# Initialize the app only if it hasn't been initialized yet
if not firebase_admin._apps:
    app = firebase_admin.initialize_app(cred, {
        'storageBucket': 'medi-go-eb65e.firebasestorage.app' 
})
db = firestore.client()
# Now we can access the bucket
bucket = storage.bucket() 