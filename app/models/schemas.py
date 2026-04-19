from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, ConfigDict


BloodType = Literal["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
Gender = Literal["Male", "Female"]
AdmissionType = Literal["Emergency", "Urgent", "Elective"]
TestResult = Literal["Normal", "Abnormal", "Inconclusive"]


class PredictionRequest(BaseModel):
    age: int = Field(..., ge=0, le=120, alias="Age")
    gender: Gender = Field(..., alias="Gender")
    blood_type: BloodType = Field(..., alias="Blood Type")
    medical_condition: str = Field(..., min_length=2, max_length=100, alias="Medical Condition")
    billing_amount: float = Field(..., ge=0, alias="Billing Amount")
    admission_type: AdmissionType = Field(..., alias="Admission Type")
    insurance_provider: str = Field(..., min_length=2, max_length=100, alias="Insurance Provider")
    medication: str = Field(..., min_length=2, max_length=100, alias="Medication")

    @field_validator("medical_condition", "insurance_provider", "medication")
    @classmethod
    def clean_strings(cls, v: str) -> str:
        return v.strip().title()

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "Age": 45,
                "Gender": "Male",
                "Blood Type": "O+",
                "Medical Condition": "Diabetes",
                "Billing Amount": 2000.50,
                "Admission Type": "Emergency",
                "Insurance Provider": "Cigna",
                "Medication": "Aspirin"
            }
        }
    )


class PredictionResponse(BaseModel):
    predicted_test_result: TestResult
    confidence: Optional[float] = Field(default=None, ge=0, le=1)
    model_version: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "predicted_test_result": "Abnormal",
                "confidence": 0.85,
                "model_version": "xgboost_v1",
                "timestamp": "2024-01-15T12:00:00Z"
            }
        }
    )


class TrainingMetrics(BaseModel):
    model_type: str = Field(..., min_length=2, max_length=50)
    accuracy: float = Field(..., ge=0, le=1)
    precision: float = Field(..., ge=0, le=1)
    recall: float = Field(..., ge=0, le=1)
    f1_score: float = Field(..., ge=0, le=1)
    confusion_matrix: list[list[int]]
    training_samples: int = Field(..., ge=1)
    test_samples: int = Field(..., ge=1)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HealthCheckResponse(BaseModel):
    status: Literal["ok", "degraded", "down"]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = "1.0.0"
    database_connected: bool
    model_loaded: bool