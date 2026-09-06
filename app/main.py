import json
import logging
import datetime
import sys
from fastapi import FastAPI, HTTPException, Response
import joblib
import pandas as pd
from app.schemas import HeartDiseaseInput

# Set up JSON logging
logger = logging.getLogger("prediction_logger")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(message)s'))
if not logger.handlers:
    logger.addHandler(handler)

app = FastAPI(title="Heart Disease API")
model = None


def map_gender(X):
    """Compatibility function required by the previously serialized model."""
    X = X.copy()
    if 'gender' in X.columns:
        X['gender'] = X['gender'].map({'male': 1, 'female': 0}).fillna(X['gender'])
    return X


# The existing joblib model was trained when map_gender belonged to __main__.
# Register it there before loading so it remains deployable without retraining.
setattr(sys.modules['__main__'], 'map_gender', map_gender)

@app.on_event("startup")
def load_model():
    global model
    try:
        model = joblib.load('models/best_model.pkl')
        logger.info(json.dumps({"event": "model_loaded", "status": "success"}))
    except Exception as e:
        logger.error(json.dumps({"event": "model_load_failed", "error": str(e)}))

@app.post("/predict")
def predict(data: HeartDiseaseInput):
    if model is None:
        raise HTTPException(status_code=503, detail="Model unavailable")
        
    input_dict = data.model_dump()
    df = pd.DataFrame([input_dict])
    
    try:
        prediction = int(model.predict(df)[0])
    except Exception as e:
        logger.error(json.dumps({"event": "prediction_failed", "error": str(e)}))
        raise HTTPException(status_code=500, detail="Prediction failed")
    
    log_data = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "input_features": input_dict,
        "prediction": prediction
    }
    logger.info(json.dumps(log_data))
    
    return {"prediction": prediction}

@app.get("/health")
def health(response: Response):
    if model is None:
        response.status_code = 503
        return {"status": "unhealthy", "reason": "model unavailable"}
    return {"status": "ok"}
