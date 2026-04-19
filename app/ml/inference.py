import logging
import os
from typing import Dict, Any, Tuple

import joblib
import numpy as np
import pandas as pd

from app.core.config import settings

logger = logging.getLogger(__name__)


class ModelInference:

    def __init__(self):
        self.model = None
        self.preprocessor = None
        self.target_encoder = None
        self.model_version = "unknown"
        self._load_model()

    def _load_model(self):
        try:
            if os.path.exists(settings.model_path):
                bundle = joblib.load(settings.model_path)
        
                if isinstance(bundle, dict) and "model" in bundle:
                    self.model = bundle["model"]
                    self.model_version = bundle.get("version", "unknown")
                    logger.info(f"Model loaded (version: {self.model_version})")
                else:
                    self.model = bundle
                    self.model_version = "legacy"
                    logger.info("Model loaded (legacy format)")

            if os.path.exists(settings.preprocessor_path):
                bundle = joblib.load(settings.preprocessor_path)

                if isinstance(bundle, dict):
                    self.preprocessor = bundle.get("preprocessor")
                    self.target_encoder = bundle.get("target_encoder")
                    logger.info("Preprocessor loaded from bundle")
                else:
                    self.preprocessor = bundle
                    logger.info("Preprocessor loaded (legacy format)")

        except Exception as e:
            logger.error(f"Model loading failed: {e}")

    def is_ready(self) -> bool:
        return self.model is not None and self.preprocessor is not None

    def _validate_input(self, input_data: Dict[str, Any]):
        if not isinstance(input_data, dict):
            raise ValueError("Input must be a dictionary")

        if len(input_data) == 0:
            raise ValueError("Empty input data")

    def predict(self, input_data: Dict[str, Any]) -> Tuple[str, float]:

        if not self.is_ready():
            raise RuntimeError("Model not ready")

        self._validate_input(input_data)

        df = pd.DataFrame([input_data])

        X = self.preprocessor.transform(df)

        probs = None
        prediction_idx = None

        if hasattr(self.model, "predict_proba"):
            probs = self.model.predict_proba(X)[0]
            prediction_idx = int(np.argmax(probs))
            confidence = float(np.max(probs))
        else:
            prediction_idx = int(self.model.predict(X)[0])
            confidence = 1.0

        prediction = self._decode_target(prediction_idx)

        return prediction, confidence

    def _decode_target(self, idx: int) -> str:
        if self.target_encoder is not None:
            return self.target_encoder.inverse_transform([idx])[0]

        return str(idx)

    def reload(self):
        self._load_model()