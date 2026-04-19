import logging
from pathlib import Path

import pandas as pd

from app.repositories.health_repository import HealthRepository
from app.ml.preprocessor import DataPreprocessor

logger = logging.getLogger(__name__)


class DataService:

    def __init__(self):
        self.repository = HealthRepository()
        self.preprocessor = DataPreprocessor()

    def _validate_file(self, file_path: str):
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if path.suffix.lower() != ".csv":
            raise ValueError("Only CSV files are supported")

        if path.stat().st_size == 0:
            raise ValueError("Empty file provided")

    async def ingest_csv(self, file_path: str) -> bool:
        try:
            self._validate_file(file_path)

            df = pd.read_csv(file_path)

            if df.empty:
                logger.warning("CSV contains no data")
                return False

            logger.info(f"Ingesting {len(df)} rows")

            success = self.repository.save_raw_data(df)

            if not success:
                logger.error("Failed to save raw data")
                return False

            await self.process_and_clean_data(df)

            return True

        except Exception as e:
            logger.error(f"CSV ingestion failed: {e}")
            return False

    async def process_and_clean_data(self, df: pd.DataFrame) -> bool:
        try:
            if df.empty:
                logger.warning("Empty dataframe passed to cleaning pipeline")
                return False

            df_clean = self.preprocessor.clean_data(df)

            if df_clean.empty:
                logger.warning("No data left after cleaning")
                return False

            return self.repository.save_cleaned_data(df_clean)

        except Exception as e:
            logger.error(f"Data cleaning failed: {e}")
            return False

    def get_training_data(self) -> pd.DataFrame:
        try:
            df = self.repository.get_cleaned_data()

            if df.empty:
                logger.warning("No training data available")

            return df

        except Exception as e:
            logger.error(f"Failed to fetch training data: {e}")
            return pd.DataFrame()