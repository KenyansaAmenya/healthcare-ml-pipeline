# load_data.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
from app.db.session import SessionLocal
from app.core.config import get_settings
from sqlalchemy import text
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_data():
    """Load healthcare data into database matching exact schema"""
    
    settings = get_settings()
    db = SessionLocal()
    
    try:
        # Load CSV file
        csv_path = settings.DATASET_PATH
        logger.info(f"Loading data from {csv_path}")
        
        if not Path(csv_path).exists():
            logger.error(f"CSV file not found at {csv_path}")
            return
        
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} records from CSV")
        
        # Clear existing data
        logger.info("Clearing existing data...")
        db.execute(text("TRUNCATE TABLE raw_healthcare_data RESTART IDENTITY CASCADE"))
        db.execute(text("TRUNCATE TABLE cleaned_healthcare_data RESTART IDENTITY CASCADE"))
        db.commit()
        
        # Insert raw data
        logger.info("Loading raw data to database...")
        inserted = 0
        
        for _, row in df.iterrows():
            # Convert date columns
            date_of_admission = None
            discharge_date = None
            
            try:
                if pd.notna(row.get('Date of Admission')):
                    date_of_admission = pd.to_datetime(row.get('Date of Admission'))
                if pd.notna(row.get('Discharge Date')):
                    discharge_date = pd.to_datetime(row.get('Discharge Date'))
            except:
                pass
            
            db.execute(
                text("""
                    INSERT INTO raw_healthcare_data 
                    (name, age, gender, blood_type, medical_condition, 
                     date_of_admission, doctor, hospital, insurance_provider, 
                     billing_amount, room_number, admission_type, discharge_date, 
                     medication, test_results, created_at)
                    VALUES (:name, :age, :gender, :blood_type, :medical_condition,
                            :date_of_admission, :doctor, :hospital, :insurance_provider,
                            :billing_amount, :room_number, :admission_type, :discharge_date,
                            :medication, :test_results, :created_at)
                """),
                {
                    'name': str(row.get('Patient Name', '')),
                    'age': int(row.get('Age', 0)) if pd.notna(row.get('Age', 0)) else 0,
                    'gender': str(row.get('Gender', '')),
                    'blood_type': str(row.get('Blood Type', '')),
                    'medical_condition': str(row.get('Medical Condition', '')),
                    'date_of_admission': date_of_admission,
                    'doctor': str(row.get('Doctor', '')),
                    'hospital': str(row.get('Hospital', '')),
                    'insurance_provider': str(row.get('Insurance Provider', '')),
                    'billing_amount': float(row.get('Billing Amount', 0)) if pd.notna(row.get('Billing Amount', 0)) else 0,
                    'room_number': int(row.get('Room Number', 0)) if pd.notna(row.get('Room Number', 0)) else 0,
                    'admission_type': str(row.get('Admission Type', '')),
                    'discharge_date': discharge_date,
                    'medication': str(row.get('Medication', '')),
                    'test_results': str(row.get('Test Result', '')),
                    'created_at': datetime.now()
                }
            )
            inserted += 1
            if inserted % 10000 == 0:
                db.commit()
                logger.info(f"  Inserted {inserted} raw records...")
        
        db.commit()
        logger.info(f" Loaded {inserted} raw records")
        
        # Insert cleaned data (only valid test results)
        logger.info("Loading cleaned data to database...")
        cleaned = 0
        
        for _, row in df.iterrows():
            test_result = row.get('Test Result', '')
            if pd.notna(test_result) and str(test_result).strip() != '':
                db.execute(
                    text("""
                        INSERT INTO cleaned_healthcare_data 
                        (age, gender, blood_type, medical_condition, billing_amount, 
                         admission_type, insurance_provider, medication, test_results, processed_at)
                        VALUES (:age, :gender, :blood_type, :medical_condition, :billing_amount,
                                :admission_type, :insurance_provider, :medication, :test_results, :processed_at)
                    """),
                    {
                        'age': int(row.get('Age', 0)) if pd.notna(row.get('Age', 0)) else 0,
                        'gender': str(row.get('Gender', '')),
                        'blood_type': str(row.get('Blood Type', '')),
                        'medical_condition': str(row.get('Medical Condition', '')),
                        'billing_amount': float(row.get('Billing Amount', 0)) if pd.notna(row.get('Billing Amount', 0)) else 0,
                        'admission_type': str(row.get('Admission Type', '')),
                        'insurance_provider': str(row.get('Insurance Provider', '')),
                        'medication': str(row.get('Medication', '')),
                        'test_results': str(test_result),
                        'processed_at': datetime.now()
                    }
                )
                cleaned += 1
                if cleaned % 10000 == 0:
                    db.commit()
                    logger.info(f"  Inserted {cleaned} cleaned records...")
        
        db.commit()
        logger.info(f" Loaded {cleaned} cleaned records")
        
        # Verify
        result = db.execute(text("SELECT COUNT(*) FROM raw_healthcare_data"))
        final_raw = result.scalar()
        result = db.execute(text("SELECT COUNT(*) FROM cleaned_healthcare_data"))
        final_cleaned = result.scalar()
        
        print("\n" + "="*50)
        print(" DATA LOADING COMPLETED!")
        print("="*50)
        print(f"Raw data records: {final_raw}")
        print(f"Cleaned data records: {final_cleaned}")
        print("="*50)
        
        # Show sample
        if final_raw > 0:
            result = db.execute(text("SELECT name, age, test_results FROM raw_healthcare_data LIMIT 1"))
            sample = result.fetchone()
            print(f"\n Sample record:")
            print(f"  Patient: {sample[0]}")
            print(f"  Age: {sample[1]}")
            print(f"  Test Result: {sample[2]}")
        
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    load_data()