import logging
from datetime import datetime, timezone
from typing import Dict, Any

from app.ml.inference import ModelInference
from app.repositories.health_repository import HealthRepository
from app.db.supabase_client import get_db

logger = logging.getLogger(__name__)


class PredictionService:

    def __init__(self):
        self.inference = ModelInference()
        self.repository = HealthRepository()

    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.inference.is_ready():
            raise RuntimeError("Model not loaded")

        try:
            prediction, confidence = self.inference.predict(input_data)

            # Log prediction to database
            self.repository.log_prediction(
                input_data=input_data,
                prediction=str(prediction),
                confidence=round(float(confidence), 4),
                model_version=self.inference.model_version
            )

            return {
                "predicted_test_result": prediction,
                "confidence": float(confidence),
                "model_version": self.inference.model_version,
                "timestamp": datetime.now(timezone.utc)
            }

        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise

    def health_check(self) -> Dict[str, Any]:
        model_loaded = self.inference.is_ready()
        
        # Check database connectivity
        db_connected = False
        try:
            db = next(get_db())
            db.execute("SELECT 1")
            db_connected = True
        except Exception as e:
            logger.warning(f"Database health check failed: {e}")
        
        status = "ok" if (model_loaded and db_connected) else "degraded" if model_loaded else "down"

        return {
            "status": status,
            "timestamp": datetime.now(timezone.utc),
            "version": "1.0.0",
            "database_connected": db_connected,
            "model_loaded": model_loaded
        }