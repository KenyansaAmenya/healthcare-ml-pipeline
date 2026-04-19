from functools import lru_cache
from typing import Optional, Any
from datetime import datetime

import pandas as pd
from supabase import create_client, Client
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

from app.core.config import settings


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


@lru_cache()
def get_supabase_client() -> Client:
    return create_client(settings.supabase_url, settings.supabase_key)


@lru_cache()
def get_supabase_admin_client() -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_key)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class SupabaseRepository:
    
    def __init__(self, table_name: str):
        self.client = get_supabase_admin_client()
        self.table = table_name
    
    def _serialize_value(self, value: Any) -> Any:
        """Serialize a single value for Supabase."""
        if isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, pd.Timestamp):
            return value.isoformat()
        elif pd.isna(value):
            return None
        return value
    
    def _serialize_record(self, data: dict) -> dict:
        """Serialize record for Supabase, handling datetime objects."""
        return {k: self._serialize_value(v) for k, v in data.items()}
    
    def insert(self, data: dict) -> dict:
        serialized = self._serialize_record(data)
        response = self.client.table(self.table).insert(serialized).execute()
        return response.data[0] if response.data else {}
    
    def insert_many(self, data: list[dict]) -> list[dict]:
        serialized_data = [self._serialize_record(record) for record in data]
        response = self.client.table(self.table).insert(serialized_data).execute()
        return response.data or []
    
    def select_all(self, limit: Optional[int] = None) -> list[dict]:
        query = self.client.table(self.table).select("*")
        if limit:
            query = query.limit(limit)
        response = query.execute()
        return response.data or []
    
    def delete_all(self) -> bool:
        self.client.table(self.table).delete().neq("id", 0).execute()
        return True