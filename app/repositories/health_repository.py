import logging
from typing import Dict, Any
from datetime import datetime

import pandas as pd

from app.db.supabase_client import SupabaseRepository

logger = logging.getLogger(__name__)


class HealthRepository:
    
    COLUMN_MAP = {
        'Name': 'name',
        'Age': 'age',
        'Gender': 'gender',
        'Blood Type': 'blood_type',
        'Medical Condition': 'medical_condition',
        'Date of Admission': 'date_of_admission',
        'Doctor': 'doctor',
        'Hospital': 'hospital',
        'Insurance Provider': 'insurance_provider',
        'Billing Amount': 'billing_amount',
        'Room Number': 'room_number',
        'Admission Type': 'admission_type',
        'Discharge Date': 'discharge_date',
        'Medication': 'medication',
        'Test Results': 'test_results'
    }
    
    REVERSE_COLUMN_MAP = {v: k for k, v in COLUMN_MAP.items()}
    
    DATE_COLUMNS = ['date_of_admission', 'discharge_date']

    def __init__(self):
        self.raw_repo = SupabaseRepository("raw_healthcare_data")
        self.cleaned_repo = SupabaseRepository("cleaned_healthcare_data")
        self.metrics_repo = SupabaseRepository("model_metrics")
        self.prediction_repo = SupabaseRepository("prediction_logs")

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.where(pd.notnull(df), None)
    
    def _parse_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Parse date columns from various formats to datetime objects."""
        df = df.copy()
        
        for col in self.DATE_COLUMNS:
            if col in df.columns:
                df[col] = pd.to_datetime(
                    df[col], 
                    format='%d/%m/%Y',
                    errors='coerce'
                )
                df[col] = df[col].where(pd.notna(df[col]), None)
        
        return df
    
    def _to_db_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert DataFrame columns from CSV format to DB snake_case format."""
        df = df.copy()
        rename_map = {k: v for k, v in self.COLUMN_MAP.items() if k in df.columns}
        if rename_map:
            df.rename(columns=rename_map, inplace=True)
        return df
    
    def _from_db_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert DataFrame columns from DB snake_case back to CSV format."""
        df = df.copy()
        rename_map = {k: v for k, v in self.REVERSE_COLUMN_MAP.items() if k in df.columns}
        if rename_map:
            df.rename(columns=rename_map, inplace=True)
        return df

    def _batch_insert(self, repo: SupabaseRepository, records: list[dict], chunk_size: int = 500) -> None:
        for i in range(0, len(records), chunk_size):
            chunk = records[i:i + chunk_size]
            chunk = [
                {
                    k: (v.isoformat() if isinstance(v, datetime) else v)
                    for k, v in record.items()
                }
                for record in chunk
            ]
            result = repo.insert_many(chunk)
            if not result:
                raise ValueError("Batch insert failed")

    def save_raw_data(self, df: pd.DataFrame) -> bool:
        try:
            if df.empty:
                logger.warning("Empty DataFrame received for raw data")
                return False

            df = self._to_db_columns(df)
            df = self._parse_dates(df)
            df = self._clean_dataframe(df)
            records = df.to_dict("records")

            self._batch_insert(self.raw_repo, records)

            logger.info(f"Saved {len(records)} raw records")
            return True

        except Exception as e:
            logger.error(f"Error saving raw data: {e}")
            return False

    def save_cleaned_data(self, df: pd.DataFrame) -> bool:
        try:
            if df.empty:
                logger.warning("Empty DataFrame received for cleaned data")
                return False

            df = self._to_db_columns(df)
            df = self._parse_dates(df)
            df = self._clean_dataframe(df)
            records = df.to_dict("records")

            self.cleaned_repo.delete_all()
            self._batch_insert(self.cleaned_repo, records)

            logger.info(f"Saved {len(records)} cleaned records")
            return True

        except Exception as e:
            logger.error(f"Error saving cleaned data: {e}")
            return False

    def get_cleaned_data(self) -> pd.DataFrame:
        try:
            data = self.cleaned_repo.select_all()
            if not data:
                logger.warning("No cleaned data found")
                return pd.DataFrame()
            
            df = pd.DataFrame(data)
            # Convert DB column names back to CSV format for ML pipeline
            df = self._from_db_columns(df)
            
            return df

        except Exception as e:
            logger.error(f"Error fetching cleaned data: {e}")
            return pd.DataFrame()

    def save_model_metrics(self, metrics: Dict[str, Any], is_active: bool = False) -> bool:
        try:
            record = {
                "model_type": metrics["model_type"],
                "accuracy": metrics["accuracy"],
                "precision": metrics["precision"],
                "recall": metrics["recall"],
                "f1_score": metrics["f1_score"],
                "confusion_matrix": metrics["confusion_matrix"],
                "training_samples": metrics["training_samples"],
                "test_samples": metrics["test_samples"],
                "is_active": is_active
            }

            result = self.metrics_repo.insert(record)
            if not result:
                raise ValueError("Metrics insert failed")

            return True

        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
            return False

    def log_prediction(
        self,
        input_data: Dict,
        prediction: str,
        confidence: float,
        model_version: str
    ) -> bool:
        try:
            record = {
                "input_data": input_data,
                "prediction": prediction,
                "confidence": confidence,
                "model_version": model_version
            }

            result = self.prediction_repo.insert(record)
            if not result:
                raise ValueError("Prediction insert failed")

            return True

        except Exception as e:
            logger.error(f"Error logging prediction: {e}")
            return False