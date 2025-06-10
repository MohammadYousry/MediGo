import tensorflow as tf
import os

# تأكد أن هذا المسار صحيح بالنسبة لمكان الملف بعد الاستنساخ
# إذا كان multitask_lab_reports_model.h5 في الجذر (المجلد الرئيسي للمشروع بعد git clone)، فسيكون هكذا:
MODEL_LOCAL_PATH = "multitask_lab_reports_model.h5"
# إذا كان في مجلد اسمه 'models' داخل مشروعك مثلاً، فسيكون:
# MODEL_LOCAL_PATH = "models/multitask_lab_reports_model.h5"

try:
    model = tf.keras.models.load_model(MODEL_LOCAL_PATH)
    print("Model loaded successfully locally!")
except Exception as e:
    print(f"Error loading model locally: {e}")
    # إذا ظهر نفس الخطأ هنا، فالمشكلة في الملف نفسه كما هو موجود على GitHub LFS.