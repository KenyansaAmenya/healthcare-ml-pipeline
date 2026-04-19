# check_data.py
from app.db.session import SessionLocal
from sqlalchemy import text

db = SessionLocal()

print("="*50)
print("RAW DATA ANALYSIS")
print("="*50)

# Check distinct test_results values
result = db.execute(text("SELECT DISTINCT test_results FROM raw_healthcare_data LIMIT 10"))
print("Distinct test_results values:")
for row in result:
    val = row[0]
    print(f"  '{val}' (length: {len(val) if val else 0})")

# Check count of non-empty test_results
result = db.execute(text("SELECT COUNT(*) FROM raw_healthcare_data WHERE test_results IS NOT NULL AND test_results != ''"))
non_empty = result.scalar()
print(f"\nRecords with non-empty test_results: {non_empty}")

# Check total records
result = db.execute(text("SELECT COUNT(*) FROM raw_healthcare_data"))
total = result.scalar()
print(f"Total records: {total}")

# Check medical conditions
result = db.execute(text("SELECT DISTINCT medical_condition FROM raw_healthcare_data LIMIT 10"))
print("\nMedical conditions:")
for row in result:
    print(f"  {row[0]}")

db.close()