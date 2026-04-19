from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, DateTime, BigInteger,
    Numeric, Boolean, Index
)
from sqlalchemy.dialects.postgresql import JSONB

from app.db.supabase_client import Base


def utc_now():
    return datetime.now(timezone.utc)


class RawHealthcareData(Base):
    __tablename__ = "raw_healthcare_data"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    name = Column(String(255), nullable=True)
    age = Column(Integer, nullable=False)
    gender = Column(String(20), nullable=False)
    blood_type = Column(String(5), nullable=False)
    medical_condition = Column(String(100), nullable=False)

    date_of_admission = Column(DateTime(timezone=True))
    doctor = Column(String(255))
    hospital = Column(String(255))

    insurance_provider = Column(String(100), nullable=False)
    billing_amount = Column(Numeric(10, 2), nullable=False)

    room_number = Column(Integer)
    admission_type = Column(String(20), nullable=False)

    discharge_date = Column(DateTime(timezone=True))
    medication = Column(String(100), nullable=False)
    test_results = Column(String(50))

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        Index("idx_raw_created_at", "created_at"),
        {"extend_existing": True},
    )


class CleanedHealthcareData(Base):
    __tablename__ = "cleaned_healthcare_data"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    age = Column(Integer, nullable=False)
    gender = Column(String(20), nullable=False)
    blood_type = Column(String(5), nullable=False)
    medical_condition = Column(String(100), nullable=False)

    billing_amount = Column(Numeric(10, 2), nullable=False)
    admission_type = Column(String(20), nullable=False)
    insurance_provider = Column(String(100), nullable=False)
    medication = Column(String(100), nullable=False)

    test_results = Column(String(50), nullable=False)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        Index("idx_cleaned_created_at", "created_at"),
        {"extend_existing": True},
    )


class ModelMetrics(Base):
    __tablename__ = "model_metrics"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    model_type = Column(String(50), nullable=False)

    accuracy = Column(Numeric(5, 4), nullable=False)
    precision = Column(Numeric(5, 4), nullable=False)
    recall = Column(Numeric(5, 4), nullable=False)
    f1_score = Column(Numeric(5, 4), nullable=False)

    confusion_matrix = Column(JSONB, nullable=False)

    training_samples = Column(Integer, nullable=False)
    test_samples = Column(Integer, nullable=False)

    is_active = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        Index("idx_model_active", "is_active"),
        {"extend_existing": True},
    )


class PredictionLog(Base):
    __tablename__ = "prediction_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    input_data = Column(JSONB, nullable=False)

    prediction = Column(String(50), nullable=False)
    confidence = Column(Numeric(5, 4))

    model_version = Column(String(50))

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        Index("idx_prediction_created_at", "created_at"),
        {"extend_existing": True},
    )