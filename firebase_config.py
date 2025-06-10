import os
import json
import firebase_admin
from firebase_admin import credentials, firestore, storage # ✅ تم إضافة 'storage'

# ✅ قم بتعريف URL لدلو التخزين الخاص بك
# استبدل 'medi-go-eb65e.firebasestorage.app' بالـ URL الفعلي لدلو التخزين الخاص بك من إعدادات مشروع Firebase.
FIREBASE_STORAGE_BUCKET_URL = 'medi-go-eb65e.firebasestorage.app'

# ✅ تهيئة Firebase مرة واحدة فقط عند بدء تشغيل التطبيق
if not firebase_admin._apps:
    if "FIREBASE_CREDENTIALS_JSON" in os.environ:
        try:
            # حاول تحميل بيانات الاعتماد من متغير البيئة
            firebase_creds = json.loads(os.environ["FIREBASE_CREDENTIALS_JSON"])
            cred = credentials.Certificate(firebase_creds)
        except json.JSONDecodeError as e:
            # ✅ معالجة الخطأ إذا كان متغير البيئة موجودًا ولكن JSON غير صالح
            print(f"ERROR: FIREBASE_CREDENTIALS_JSON environment variable contains invalid JSON: {e}", file=sys.stderr)
            raise ValueError("Invalid Firebase credentials JSON provided in environment variable.") from e
    else:
        # ✅ إذا لم يتم العثور على متغير البيئة، اطبع رسالة واخرج (يُفضل في بيئة الإنتاج)
        print("ERROR: FIREBASE_CREDENTIALS_JSON environment variable not found. Cannot initialize Firebase.", file=sys.stderr)
        raise Exception("Firebase credentials environment variable is missing.") # ✅ رسالة خطأ أوضح

    # ✅ قم بتهيئة Firebase مع تحديد دلو التخزين
    firebase_admin.initialize_app(cred, {
        'storageBucket': FIREBASE_STORAGE_BUCKET_URL
    })

# ✅ العملاء الجاهزون
db = firestore.client()
bucket = storage.bucket() # ✅ الآن يمكنك الوصول إلى دلو التخزين
