"""
scripts/generate_sample_data.py
Generates realistic sample Aadhaar enrollment, demographic, and biometric datasets
for local testing and database population.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import sys
from pathlib import Path
import argparse

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

REGIONS = [
    ('MH-MUM', 'Maharashtra', 'Mumbai'),
    ('MH-PUN', 'Maharashtra', 'Pune'),
    ('MH-NSK', 'Maharashtra', 'Nashik'),
    ('KA-BLR', 'Karnataka', 'Bengaluru'),
    ('KA-MYS', 'Karnataka', 'Mysuru'),
    ('TN-CHN', 'Tamil Nadu', 'Chennai'),
    ('TN-CBE', 'Tamil Nadu', 'Coimbatore'),
    ('UP-LKO', 'Uttar Pradesh', 'Lucknow'),
    ('UP-AGR', 'Uttar Pradesh', 'Agra'),
    ('DL-NDL', 'Delhi', 'New Delhi'),
]

GENDERS = ['Male', 'Female', 'Other']
AGE_GROUPS = ['0-18', '19-35', '36-60', '60+']
ENROLLMENT_STATUSES = ['Pending', 'Verified', 'Rejected', 'Generated']
UPDATE_TYPES = ['Name', 'Address', 'Mobile', 'Email', 'Biometric', 'Photo', 'DOB']
UPDATE_STATUSES = ['Pending', 'Approved', 'Rejected']


def generate_enrollment_data(num_records=5000, days_back=365):
    """Generate realistic enrollment dataset."""
    print(f"Generating {num_records} enrollment records...")
    
    data = []
    start_date = datetime.now() - timedelta(days=days_back)
    
    for i in range(num_records):
        enrollment_date = start_date + timedelta(
            days=random.randint(0, days_back),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        # Bias towards 'Generated' status (70% success rate)
        status = random.choices(
            ENROLLMENT_STATUSES,
            weights=[10, 50, 20, 20],
            k=1
        )[0]
        
        data.append({
            'enrollment_date': enrollment_date.date(),
            'gender': random.choice(GENDERS),
            'age': random.randint(5, 95),
            'enrollment_status': status,
            'aadhaar_generated': status == 'Generated',
            'region_code': random.choice(REGIONS)[0],
            'district': random.choice(REGIONS)[2],
        })
    
    df = pd.DataFrame(data)
    output_path = Path(__file__).parent.parent / 'data' / 'api_data_aadhar_enrolment.csv'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"✓ Enrollment data saved to {output_path}")
    return df


def generate_demographic_data(num_records=3000, days_back=365):
    """Generate realistic demographic/update dataset."""
    print(f"Generating {num_records} demographic/update records...")
    
    data = []
    start_date = datetime.now() - timedelta(days=days_back)
    
    for i in range(num_records):
        update_date = start_date + timedelta(
            days=random.randint(0, days_back),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        # Bias towards 'Approved' status (60%)
        status = random.choices(
            UPDATE_STATUSES,
            weights=[20, 60, 20],
            k=1
        )[0]
        
        data.append({
            'update_date': update_date.date(),
            'update_type': random.choice(UPDATE_TYPES),
            'update_status': status,
            'region_code': random.choice(REGIONS)[0],
            'district': random.choice(REGIONS)[2],
        })
    
    df = pd.DataFrame(data)
    output_path = Path(__file__).parent.parent / 'data' / 'api_data_aadhar_demographic.csv'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"✓ Demographic data saved to {output_path}")
    return df


def generate_biometric_data(num_records=4500, days_back=365):
    """Generate realistic biometric quality dataset."""
    print(f"Generating {num_records} biometric quality records...")
    
    data = []
    start_date = datetime.now() - timedelta(days=days_back)
    
    for i in range(num_records):
        enrollment_date = start_date + timedelta(
            days=random.randint(0, days_back),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        # Quality scores: mostly 70-95, some outliers below 60
        if random.random() < 0.1:  # 10% poor quality
            fp_quality = random.randint(30, 60)
        else:
            fp_quality = random.randint(70, 98)
        
        if random.random() < 0.12:
            iris_quality = random.randint(25, 60)
        else:
            iris_quality = random.randint(70, 98)
        
        if random.random() < 0.08:
            photo_quality = random.randint(40, 65)
        else:
            photo_quality = random.randint(75, 99)
        
        data.append({
            'enrollment_date': enrollment_date.date(),
            'fingerprint_quality': fp_quality,
            'iris_quality': iris_quality,
            'photo_quality': photo_quality,
        })
    
    df = pd.DataFrame(data)
    output_path = Path(__file__).parent.parent / 'data' / 'api_data_aadhar_biometric.csv'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"✓ Biometric data saved to {output_path}")
    return df


def main(years: int = 1, days: int | None = None):
    """Generate all sample datasets.

    Args:
        years: number of years to span (approximate, each year = 365 days)
        days: exact days_back to use (overrides years when provided)
    """
    print("=" * 60)
    print("AADHAAR PORTAL - SAMPLE DATA GENERATOR")
    print("=" * 60)

    days_back = days if days is not None else max(1, years * 365)

    # Generate datasets
    generate_enrollment_data(num_records=5000, days_back=days_back)
    generate_demographic_data(num_records=3000, days_back=days_back)
    generate_biometric_data(num_records=4500, days_back=days_back)

    print("\n" + "=" * 60)
    print("✓ ALL SAMPLE DATASETS GENERATED SUCCESSFULLY")
    print("=" * 60)
    print("\nDatasets created in ./data/ directory:")
    print("  - api_data_aadhar_enrolment.csv (5000 records)")
    print("  - api_data_aadhar_demographic.csv (3000 records)")
    print("  - api_data_aadhar_biometric.csv (4500 records)")
    print("\nUse these files with the data import API endpoints:")
    print("  POST /api/import/enrollments/upload")
    print("  POST /api/import/demographic/upload")
    print("  POST /api/import/biometric/upload")
    print("\n" + "=" * 60)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate Aadhaar sample datasets')
    parser.add_argument('--years', type=int, default=1, help='Number of years to span (approx)')
    parser.add_argument('--days', type=int, help='Exact number of days_back to use (overrides years)')
    args = parser.parse_args()
    main(years=args.years, days=args.days)
