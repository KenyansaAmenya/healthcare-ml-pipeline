# generate_and_clean.py
import pandas as pd
import numpy as np
from app.db.session import SessionLocal
from sqlalchemy import text
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_test_results_and_clean():
    """Generate test results based on medical conditions and clean data"""
    
    db = SessionLocal()
    
    try:
        # Load raw data
        logger.info("Loading raw data...")
        df = pd.read_sql(text("SELECT * FROM raw_healthcare_data"), db.bind)
        logger.info(f"Loaded {len(df)} records")
        
        # Define mapping from medical condition to test result
        # Based on typical healthcare patterns
        condition_test_mapping = {
            'Cancer': 'Abnormal',      # Cancer usually shows abnormal results
            'Diabetes': 'Abnormal',    # Diabetes shows abnormal blood sugar
            'Hypertension': 'Abnormal', # High blood pressure is abnormal
            'Obesity': 'Abnormal',      # Obesity often shows abnormal markers
            'Asthma': 'Inconclusive',   # Asthma can be intermittent
            'Arthritis': 'Inconclusive', # Arthritis may show inflammation
            'Stroke': 'Abnormal',       # Stroke shows clear abnormalities
            'Infection': 'Abnormal',    # Infection shows abnormal counts
            'Migraine': 'Normal',       # Migraine often shows normal tests
            'Alzheimer\'s': 'Abnormal'  # Alzheimer's shows cognitive markers
        }
        
        # Generate test results
        logger.info("Generating test results based on medical conditions...")
        df['test_results'] = df['medical_condition'].map(condition_test_mapping)
        
        # Fill any missing with Inconclusive
        df['test_results'] = df['test_results'].fillna('Inconclusive')
        
        # Add some realistic randomness (15% variation)
        np.random.seed(42)
        random_idx = np.random.choice(df.index, size=int(len(df)*0.15), replace=False)
        
        # For random variation, slightly shift the results
        for idx in random_idx:
            current = df.loc[idx, 'test_results']
            if current == 'Normal':
                df.loc[idx, 'test_results'] = np.random.choice(['Normal', 'Inconclusive'], p=[0.7, 0.3])
            elif current == 'Abnormal':
                df.loc[idx, 'test_results'] = np.random.choice(['Abnormal', 'Inconclusive'], p=[0.8, 0.2])
            else:  # Inconclusive
                df.loc[idx, 'test_results'] = np.random.choice(['Normal', 'Abnormal', 'Inconclusive'], p=[0.2, 0.3, 0.5])
        
        # Show distribution
        logger.info("\n Generated Test Result Distribution:")
        dist = df['test_results'].value_counts()
        for result, count in dist.items():
            percentage = (count/len(df))*100
            bar = '█' * int(percentage/2)
            logger.info(f"  {result:12} : {count:6} ({percentage:5.1f}%) {bar}")
        
        # Prepare cleaned data
        logger.info("\n Cleaning and preparing data...")
        cleaned_df = pd.DataFrame()
        cleaned_df['age'] = df['age']
        cleaned_df['gender'] = df['gender'].str.upper().str.strip()
        cleaned_df['blood_type'] = df['blood_type'].str.upper().str.strip().fillna('UNKNOWN')
        cleaned_df['medical_condition'] = df['medical_condition'].fillna('None')
        cleaned_df['billing_amount'] = df['billing_amount'].fillna(df['billing_amount'].median())
        cleaned_df['admission_type'] = df['admission_type'].str.capitalize().str.strip().fillna('Emergency')
        cleaned_df['insurance_provider'] = df['insurance_provider'].fillna('Self Pay')
        cleaned_df['medication'] = df['medication'].fillna('None')
        cleaned_df['test_results'] = df['test_results']
        cleaned_df['processed_at'] = datetime.now()
        
        # Remove invalid data
        before = len(cleaned_df)
        cleaned_df = cleaned_df[cleaned_df['age'].between(0, 120)]
        cleaned_df = cleaned_df[cleaned_df['billing_amount'] >= 0]
        cleaned_df = cleaned_df[cleaned_df['gender'].isin(['MALE', 'FEMALE'])]
        cleaned_df = cleaned_df.dropna(subset=['age', 'gender', 'test_results'])
        after = len(cleaned_df)
        
        logger.info(f"  Removed {before - after} invalid records")
        logger.info(f"  Final cleaned records: {after}")
        
        # Clear existing cleaned data
        logger.info("\n Clearing existing cleaned_healthcare_data table...")
        db.execute(text("TRUNCATE TABLE cleaned_healthcare_data RESTART IDENTITY CASCADE"))
        db.commit()
        
        # Insert cleaned data in batches
        logger.info(" Inserting cleaned data into database...")
        batch_size = 5000
        inserted = 0
        
        for i in range(0, len(cleaned_df), batch_size):
            batch = cleaned_df.iloc[i:i+batch_size]
            for _, row in batch.iterrows():
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
                        'processed_at': row['processed_at']
                    }
                )
                inserted += 1
            
            db.commit()
            logger.info(f" Inserted {inserted:,} / {len(cleaned_df):,} records")
        
        # Verify final distribution
        result = db.execute(text("""
            SELECT test_results, COUNT(*) as count 
            FROM cleaned_healthcare_data 
            GROUP BY test_results 
            ORDER BY count DESC
        """))
        
        print("\n" + "="*60)
        print(" DATA PREPARATION COMPLETED SUCCESSFULLY!")
        print("="*60)
        print(" Final Test Result Distribution in Database:")
        for row in result:
            count = row[1]
            percentage = (count/len(cleaned_df))*100
            bar = '█' * int(percentage/2)
            print(f"  {row[0]:12} : {count:6,} ({percentage:5.1f}%) {bar}")
        print("="*60)
        
        # Show sample records
        print("\n Sample of cleaned data:")
        sample = db.execute(text("""
            SELECT age, gender, medical_condition, test_results 
            FROM cleaned_healthcare_data 
            LIMIT 5
        """))
        for row in sample:
            print(f"  Age: {row[0]:3} | Gender: {row[1]:5} | Condition: {row[2]:15} | Result: {row[3]}")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    generate_test_results_and_clean()