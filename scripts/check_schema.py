# check_schema.py
from app.db.session import sync_engine
from sqlalchemy import inspect

inspector = inspect(sync_engine)

print("Raw healthcare data columns:")
for col in inspector.get_columns('raw_healthcare_data'):
    print(f"  {col['name']} ({col['type']})")

print("\nCleaned healthcare data columns:")
for col in inspector.get_columns('cleaned_healthcare_data'):
    print(f"  {col['name']} ({col['type']})")