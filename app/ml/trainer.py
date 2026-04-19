import logging
from typing import Dict, Any, Tuple

import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, confusion_matrix
)
import xgboost as xgb

logger = logging.getLogger(__name__)


class ModelTrainer:

    def __init__(self, test_size: float = 0.2, random_state: int = 42):
        self.test_size = test_size
        self.random_state = random_state

        self.models: Dict[str, Dict] = {}
        self.best_model = None
        self.best_model_name = None
        self.metrics: Dict[str, Any] = {}

    def train_models(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:

        if len(X) == 0 or len(y) == 0:
            raise ValueError("Empty training data")

        if len(np.unique(y)) < 2:
            raise ValueError("Need at least 2 classes for classification")

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=self.test_size,
            random_state=self.random_state,
            stratify=y
        )

        logger.info(f"Train: {X_train.shape}, Test: {X_test.shape}")

        num_classes = len(np.unique(y))

        models = {
            "xgboost": xgb.XGBClassifier(
                objective="multi:softprob",
                num_class=num_classes,
                eval_metric="mlogloss",
                n_estimators=150,
                max_depth=6,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=self.random_state,
                n_jobs=-1,
                verbosity=0
            ),
            "random_forest": RandomForestClassifier(
                n_estimators=200,
                max_depth=12,
                class_weight="balanced",
                random_state=self.random_state,
                n_jobs=-1
            )
        }

        best_f1 = -1

        for name, model in models.items():
            logger.info(f"Training {name}")

            model.fit(X_train, y_train)

            y_pred = model.predict(X_test)

            metrics = self._calculate_metrics(y_test, y_pred)
            metrics["model_type"] = name
            metrics["training_samples"] = len(X_train)
            metrics["test_samples"] = len(X_test)

            self.models[name] = {
                "model": model,
                "metrics": metrics
            }

            logger.info(
                f"{name} | F1: {metrics['f1_score']:.4f} | "
                f"Acc: {metrics['accuracy']:.4f}"
            )

            if metrics["f1_score"] > best_f1:
                best_f1 = metrics["f1_score"]
                self.best_model = model
                self.best_model_name = name
                self.metrics = metrics

        logger.info(f"Best model: {self.best_model_name} (F1={best_f1:.4f})")

        return self.metrics

    def _calculate_metrics(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, Any]:
        return {
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "precision": float(precision_score(y_true, y_pred, average="weighted", zero_division=0)),
            "recall": float(recall_score(y_true, y_pred, average="weighted", zero_division=0)),
            "f1_score": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
            "confusion_matrix": confusion_matrix(y_true, y_pred).tolist()
        }

    def predict_with_confidence(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        if self.best_model is None:
            raise ValueError("Model not trained")

        preds = self.best_model.predict(X)

        if hasattr(self.best_model, "predict_proba"):
            probs = self.best_model.predict_proba(X)
            confidence = np.max(probs, axis=1)
        else:
            confidence = np.ones(len(preds))

        return preds, confidence

    def get_best_model(self) -> Tuple[Any, str, Dict]:
        if self.best_model is None:
            raise ValueError("No model trained yet")

        return self.best_model, self.best_model_name, self.metrics