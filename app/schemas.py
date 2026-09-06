from pydantic import BaseModel, Field

class HeartDiseaseInput(BaseModel):
    age: float = Field(..., ge=0, le=120)
    gender: str = Field(..., description="'male' or 'female'")
    cp: int = Field(..., ge=0, le=3)
    trestbps: float = Field(..., ge=0)
    chol: float = Field(..., ge=0)
    fbs: int = Field(..., ge=0, le=1)
    restecg: int = Field(..., ge=0, le=2)
    thalach: float = Field(..., ge=0)
    exang: int = Field(..., ge=0, le=1)
    oldpeak: float = Field(..., ge=0.0)
    slope: int = Field(..., ge=0, le=2)
    ca: int = Field(..., ge=0, le=4)
    thal: int = Field(..., ge=0, le=3)
