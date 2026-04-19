from fastapi import APIRouter, HTTPException, Request, Depends

from app.models.schemas import PredictionRequest, PredictionResponse, HealthCheckResponse
from app.services.prediction_service import PredictionService
from app.core.security import limiter

router = APIRouter(prefix="/api/v1", tags=["predictions"])


def get_prediction_service():
    return PredictionService()


@router.post("/predict", response_model=PredictionResponse)
@limiter.limit("10/minute")
async def predict(
    request: Request,
    data: PredictionRequest,
    service: PredictionService = Depends(get_prediction_service)
):
    try:
        input_dict = {
            "Age": data.age,
            "Gender": data.gender,
            "Blood Type": data.blood_type,
            "Medical Condition": data.medical_condition,
            "Billing Amount": data.billing_amount,
            "Admission Type": data.admission_type,
            "Insurance Provider": data.insurance_provider,
            "Medication": data.medication
        }

        result = service.predict(input_dict)

        return PredictionResponse(**result)

    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal prediction error")


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(service: PredictionService = Depends(get_prediction_service)):
    try:
        health = service.health_check()
        return HealthCheckResponse(**health)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ready")
async def readiness_check(service: PredictionService = Depends(get_prediction_service)):
    if service.inference.is_ready():
        return {"status": "ready"}

    raise HTTPException(status_code=503, detail="Model not loaded")