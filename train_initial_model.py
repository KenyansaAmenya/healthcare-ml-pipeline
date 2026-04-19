import asyncio
import sys
import logging
from pathlib import Path
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


DATA_PATH = "./data/healthcare_dataset.csv"


def validate_file(path: str):
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    if file_path.stat().st_size == 0:
        raise ValueError("Dataset file is empty")

    return file_path


async def main():
    from app.services.training_service import TrainingService

    start_time = time.time()

    service = TrainingService()

    try:
        file_path = validate_file(DATA_PATH)

        logger.info(f"Starting training from {file_path}")

        metrics = await service.initial_training(str(file_path))

        duration = time.time() - start_time

        logger.info("Training completed successfully")
        logger.info(f"Model: {metrics['model_type']}")
        logger.info(f"F1 Score: {metrics['f1_score']:.4f}")
        logger.info(f"Accuracy: {metrics['accuracy']:.4f}")
        logger.info(f"Training Time: {duration:.2f}s")

        return 0

    except Exception as e:
        logger.exception(f"Training failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))