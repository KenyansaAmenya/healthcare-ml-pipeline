import logging
from typing import Tuple, List

import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer

logger = logging.getLogger(__name__)


class DataPreprocessor:

    DROP_COLUMNS = [
        'Name', 'Doctor', 'Hospital',
        'Room Number', 'Date of Admission', 'Discharge Date'
    ]

    CATEGORICAL_COLUMNS = [
        'Gender', 'Blood Type', 'Medical Condition',
        'Admission Type', 'Insurance Provider', 'Medication'
    ]

    NUMERICAL_COLUMNS = ['Age', 'Billing Amount']

    TARGET_COLUMN = 'Test Results'

    def __init__(self):
        self.target_encoder = LabelEncoder()
        self.preprocessor: ColumnTransformer | None = None
        self.feature_names: List[str] = []

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info(f"Cleaning data: {df.shape}")

        df = df.copy()

        df.drop(columns=[c for c in self.DROP_COLUMNS if c in df.columns],
                inplace=True, errors='ignore')

        df.replace({np.nan: None}, inplace=True)

        for col in self.CATEGORICAL_COLUMNS:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().str.title()

        for col in self.NUMERICAL_COLUMNS:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        if 'Billing Amount' in df.columns:
            df = df[df['Billing Amount'].fillna(0) >= 0]

        df.drop_duplicates(inplace=True)

        logger.info(f"After cleaning: {df.shape}")

        return df

    def _validate_columns(self, df: pd.DataFrame):
        required = set(self.CATEGORICAL_COLUMNS + self.NUMERICAL_COLUMNS + [self.TARGET_COLUMN])
        missing = required - set(df.columns)

        if missing:
            raise ValueError(f"Missing required columns: {missing}")

    def fit_transform(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        df = self.clean_data(df)
        self._validate_columns(df)

        X = df.drop(self.TARGET_COLUMN, axis=1)
        y = df[self.TARGET_COLUMN].astype(str).str.strip().str.title()

        categorical_features = [c for c in self.CATEGORICAL_COLUMNS if c in X.columns]
        numerical_features = [c for c in self.NUMERICAL_COLUMNS if c in X.columns]

        transformers = []

        if numerical_features:
            transformers.append(
                ("num", StandardScaler(), numerical_features)
            )

        if categorical_features:
            transformers.append(
                ("cat", OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_features)
            )

        self.preprocessor = ColumnTransformer(transformers, remainder='drop')

        X_transformed = self.preprocessor.fit_transform(X)
        y_encoded = self.target_encoder.fit_transform(y)

        self.feature_names = self._get_feature_names(categorical_features, numerical_features)

        logger.info(f"Features shape: {X_transformed.shape}")
        logger.info(f"Classes: {list(self.target_encoder.classes_)}")

        return X_transformed, y_encoded

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        if self.preprocessor is None:
            raise ValueError("Preprocessor not fitted")

        df = self.clean_data(df)

        X = df.copy()
        if self.TARGET_COLUMN in X.columns:
            X = X.drop(self.TARGET_COLUMN, axis=1)

        return self.preprocessor.transform(X)

    def inverse_transform_target(self, y: np.ndarray) -> np.ndarray:
        return self.target_encoder.inverse_transform(y)

    def _get_feature_names(self, categorical_features, numerical_features):
        feature_names = list(numerical_features)

        if categorical_features:
            cat_encoder = self.preprocessor.named_transformers_["cat"]
            cat_names = cat_encoder.get_feature_names_out(categorical_features)
            feature_names.extend(cat_names.tolist())

        return feature_names

    def get_target_classes(self) -> List[str]:
        return list(self.target_encoder.classes_)