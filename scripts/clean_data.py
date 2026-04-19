# clean_data.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import numpy as np
from app.db.session import SessionLocal
from app.core.config import get_settings
from sqlalchemy import text
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_data():
    """Clean and validate healthcare data"""
    
    settings = get_settings()
    db = SessionLocal()
    
    try:
        # Load raw data from database
        logger.info("Loading raw data from database...")
        query = text("SELECT * FROM raw_healthcare_data")
        df = pd.read_sql(query, db.bind)
        
        if df.empty:
            logger.error("No raw data found. Please run load_data.py first")
            return
        
        logger.info(f"Loaded {len(df)} raw records")
        
        # Make a copy for cleaning
        df_cleaned = df.copy()
        initial_count = len(df_cleaned)
        
        # 1. Remove duplicates
        duplicates = df_cleaned.duplicated(subset=['name', 'date_of_admission', 'test_results']).sum()
        df_cleaned = df_cleaned.drop_duplicates(subset=['name', 'date_of_admission', 'test_results'])
        logger.info(f"Removed {duplicates} duplicate records")
        
        # 2. Handle missing values
        # Fill missing test_results with 'Inconclusive'
        df_cleaned['test_results'] = df_cleaned['test_results'].fillna('Inconclusive')
        
        # Fill missing age with median
        median_age = df_cleaned['age'].median()
        df_cleaned['age'] = df_cleaned['age'].fillna(median_age)
        
        # Fill missing gender with mode
        mode_gender = df_cleaned['gender'].mode()[0] if not df_cleaned['gender'].mode().empty else 'Unknown'
        df_cleaned['gender'] = df_cleaned['gender'].fillna(mode_gender)
        
        # Fill missing blood_type with 'Unknown'
        df_cleaned['blood_type'] = df_cleaned['blood_type'].fillna('Unknown')
        
        # Fill missing medical_condition with 'None'
        df_cleaned['medical_condition'] = df_cleaned['medical_condition'].fillna('None')
        
        # Fill missing billing_amount with median
        median_billing = df_cleaned['billing_amount'].median()
        df_cleaned['billing_amount'] = df_cleaned['billing_amount'].fillna(median_billing)
        
        # Fill missing admission_type with 'Emergency'
        df_cleaned['admission_type'] = df_cleaned['admission_type'].fillna('Emergency')
        
        # Fill missing insurance_provider with 'Self Pay'
        df_cleaned['insurance_provider'] = df_cleaned['insurance_provider'].fillna('Self Pay')
        
        # Fill missing medication with 'None'
        df_cleaned['medication'] = df_cleaned['medication'].fillna('None')
        
        missing_count = initial_count - len(df_cleaned)
        logger.info(f"Handled missing values, {missing_count} records affected")
        
        # 3. Validate and correct data types
        # Age validation (0-120)
        invalid_age = df_cleaned[(df_cleaned['age'] < 0) | (df_cleaned['age'] > 120)].shape[0]
        df_cleaned['age'] = df_cleaned['age'].clip(0, 120)
        logger.info(f"Corrected {invalid_age} invalid age values")
        
        # Billing amount validation (non-negative)
        invalid_billing = df_cleaned[df_cleaned['billing_amount'] < 0].shape[0]
        df_cleaned['billing_amount'] = df_cleaned['billing_amount'].abs()
        logger.info(f"Corrected {invalid_billing} negative billing amounts")
        
        # Room number validation (1-1000)
        invalid_room = df_cleaned[(df_cleaned['room_number'] < 1) | (df_cleaned['room_number'] > 1000)].shape[0]
        df_cleaned['room_number'] = df_cleaned['room_number'].clip(1, 1000)
        logger.info(f"Corrected {invalid_room} invalid room numbers")
        
        # 4. Standardize text fields
        # Gender standardization
        df_cleaned['gender'] = df_cleaned['gender'].str.upper().str.strip()
        df_cleaned['gender'] = df_cleaned['gender'].replace({
            'M': 'MALE', 'F': 'FEMALE', 'MALE': 'MALE', 'FEMALE': 'FEMALE'
        })
        
        # Blood type standardization
        df_cleaned['blood_type'] = df_cleaned['blood_type'].str.upper().str.strip()
        
        # Test results standardization
        df_cleaned['test_results'] = df_cleaned['test_results'].str.capitalize().str.strip()
        valid_results = ['Normal', 'Abnormal', 'Inconclusive']
        df_cleaned['test_results'] = df_cleaned['test_results'].apply(
            lambda x: x if x in valid_results else 'Inconclusive'
        )
        
        # Admission type standardization
        df_cleaned['admission_type'] = df_cleaned['admission_type'].str.capitalize().str.strip()
        
        # 5. Remove outliers (age > 100 or billing > 1M)
        outliers_age = df_cleaned[df_cleaned['age'] > 100].shape[0]
        outliers_billing = df_cleaned[df_cleaned['billing_amount'] > 1000000].shape[0]
        df_cleaned = df_cleaned[df_cleaned['age'] <= 100]
        df_cleaned = df_cleaned[df_cleaned['billing_amount'] <= 1000000]
        logger.info(f"Removed {outliers_age} age outliers and {outliers_billing} billing outliers")
        
        # 6. Remove records with missing critical fields
        critical_fields = ['name', 'age', 'gender', 'test_results']
        before_critical = len(df_cleaned)
        df_cleaned = df_cleaned.dropna(subset=critical_fields)
        critical_removed = before_critical - len(df_cleaned)
        logger.info(f"Removed {critical_removed} records with missing critical fields")
        
        # 7. Calculate derived fields (if needed)
        df_cleaned['year_of_admission'] = pd.to_datetime(df_cleaned['date_of_admission']).dt.year
        df_cleaned['age_group'] = pd.cut(df_cleaned['age'], 
                                          bins=[0, 18, 35, 50, 65, 120],
                                          labels=['Child', 'Young Adult', 'Adult', 'Middle Age', 'Senior'])
        
        # 8. Final statistics
        final_count = len(df_cleaned)
        total_removed = initial_count - final_count
        
        logger.info("\n" + "="*50)
        logger.info("CLEANING SUMMARY")
        logger.info("="*50)
        logger.info(f"Initial records: {initial_count}")
        logger.info(f"Final records: {final_count}")
        logger.info(f"Records removed: {total_removed} ({total_removed/initial_count*100:.1f}%)")
        logger.info(f"Test result distribution:")
        for result in df_cleaned['test_results'].value_counts().items():
            logger.info(f"  {result[0]}: {result[1]} ({result[1]/final_count*100:.1f}%)")
        
        # 9. Save cleaned data to database
        logger.info("\nSaving cleaned data to database...")
        
        # Clear existing cleaned data
        db.execute(text("TRUNCATE TABLE cleaned_healthcare_data RESTART IDENTITY CASCADE"))
        db.commit()
        
        # Insert cleaned data
        cleaned_records = 0
        for _, row in df_cleaned.iterrows():
            db.execute(
                text("""
                    INSERT INTO cleaned_healthcare_data 
                    (age, gender, blood_type, medical_condition, billing_amount, 
                     admission_type, insurance_provider, medication, test_results, processed_at)
                    VALUES (:age, :gender, :blood_type, :medical_condition, :billing_amount,
                            :admission_type, :insurance_provider, :medication, :test_results, :processed_at)
                """),
                {
                    'age': int(row['age']),
                    'gender': str(row['gender']),
                    'blood_type': str(row['blood_type']),
                    'medical_condition': str(row['medical_condition']),
                    'billing_amount': float(row['billing_amount']),
                    'admission_type': str(row['admission_type']),
                    'insurance_provider': str(row['insurance_provider']),
                    'medication': str(row['medication']),
                    'test_results': str(row['test_results']),
                    'processed_at': datetime.now()
                }
            )
            cleaned_records += 1
            if cleaned_records % 10000 == 0:
                db.commit()
                logger.info(f"  Saved {cleaned_records} cleaned records...")
        
        db.commit()
        
        # Verify
        result = db.execute(text("SELECT COUNT(*) FROM cleaned_healthcare_data"))
        final_db_count = result.scalar()
        
        print("\n" + "="*50)
        print(" DATA CLEANING COMPLETED!")
        print("="*50)
        print(f"Cleaned records in database: {final_db_count}")
        print("="*50)
        
        # Save summary to file
        summary_path = Path(settings.MODEL_PATH) / "cleaning_summary.txt"
        summary_path.parent.mkdir(exist_ok=True)
        with open(summary_path, 'w') as f:
            f.write(f"Data Cleaning Summary\n")
            f.write(f"===================\n")
            f.write(f"Date: {datetime.now()}\n")
            f.write(f"Initial records: {initial_count}\n")
            f.write(f"Final records: {final_count}\n")
            f.write(f"Records removed: {total_removed}\n")
            f.write(f"\nTest Result Distribution:\n")
            for result, count in df_cleaned['test_results'].value_counts().items():
                f.write(f"  {result}: {count} ({count/final_count*100:.1f}%)\n")
        
        logger.info(f"Cleaning summary saved to {summary_path}")
        
    except Exception as e:
        logger.error(f"Error cleaning data: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    clean_data()