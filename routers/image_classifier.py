import io
import numpy as np
from PIL import Image
from main import load_multitask_model, model

def classify_radiology_image(image_bytes, img_size=(224, 224)):
    try:
        # Ensure the model is loaded before prediction
        load_multitask_model()

        # Preprocess the image
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image = image.resize(img_size)
        img_array = np.expand_dims(np.array(image) / 255.0, axis=0)

        # Predict
        prediction = model.predict(img_array)
        confidence = float(prediction[0][0])
        is_valid = confidence > 0.5

        return {
            "is_valid": is_valid,
            "confidence": round(confidence, 4)
        }
    except Exception as e:
        return {
            "is_valid": None,
            "confidence": None,
            "error": str(e)
        }
