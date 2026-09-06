from fastapi.testclient import TestClient
import app.main as main_app

# Fake the model for tests
class DummyModel:
    def predict(self, df):
        return [1]

main_app.model = DummyModel()
client = TestClient(main_app.app)

def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

def test_health_no_model():
    main_app.model = None
    resp = client.get("/health")
    assert resp.status_code == 503
    main_app.model = DummyModel() # restore

def test_predict_valid():
    payload = {"age": 50, "gender": "male", "cp": 1, "trestbps": 120, "chol": 200, "fbs": 0, "restecg": 1, "thalach": 150, "exang": 0, "oldpeak": 1.0, "slope": 1, "ca": 0, "thal": 2}
    resp = client.post("/predict", json=payload)
    assert resp.status_code == 200
    assert "prediction" in resp.json()

def test_predict_invalid():
    payload = {"age": 150} # invalid age
    resp = client.post("/predict", json=payload)
    assert resp.status_code == 422
