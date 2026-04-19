import logging
import os
import joblib
from datetime import datetime, timezone

from app.core.config import settings
from app.services.data_service import DataService
from app.ml.trainer import ModelTrainer
from app.ml.preprocessor import DataPreprocessor
from app.repositories.health_repository import HealthRepository

logger = logging.getLogger(__name__)


class TrainingService:

    def __init__(self):
        self.data_service = DataService()
        self.repository = HealthRepository()
        self.preprocessor = DataPreprocessor()
        self.trainer = ModelTrainer()

    async def retrain_model(self) -> dict:
        logger.info("Starting retraining pipeline")

        df = self.data_service.get_training_data()

        if df is None or df.empty:
            raise ValueError("No training data available")

        X, y = self.preprocessor.fit_transform(df)

        metrics = self.trainer.train_models(X, y)

        model, model_name, final_metrics = self.trainer.get_best_model()

        os.makedirs(os.path.dirname(settings.model_path), exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        model_bundle = {
            "model": model,
            "version": f"{model_name}_{timestamp}",
            "metrics": final_metrics
        }

        preprocessor_bundle = {
            "preprocessor": self.preprocessor,
            "target_encoder": self.preprocessor.target_encoder,
            "version": timestamp
        }

        joblib.dump(model_bundle, settings.model_path)
        joblib.dump(preprocessor_bundle, settings.preprocessor_path)

        logger.info(f"Model saved: {model_name}")

        metrics_record = {
            **final_metrics,
            "model_type": model_name,
            "created_at": timestamp
        }

        self.repository.save_model_metrics(metrics_record, is_active=True)

        return metrics_record

    async def initial_training(self, csv_path: str) -> dict:
        logger.info(f"Initial training from {csv_path}")

        success = await self.data_service.ingest_csv(csv_path)

        if not success:
            raise RuntimeError("Data ingestion failed")

        return await self.retrain_model()