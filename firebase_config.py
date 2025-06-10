import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

if "FIREBASE_CREDENTIALS_JSON" in os.environ:
    firebase_creds = json.loads(os.environ["FIREBASE_CREDENTIALS_JSON"])
    cred = credentials.Certificate(firebase_creds)
else:
    raise Exception("FIREBASE_CREDENTIALS_JSON env var not found")

firebase_admin.initialize_app(cred)
db = firestore.client()
