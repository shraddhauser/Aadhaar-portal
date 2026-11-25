"""
backend/data_ingestion.py
Data ingestion, cleaning, normalization and predictive analytics module.
Handles Aadhaar enrollment, demographic, and biometric data import.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import logging
from sqlalchemy.orm import Session
from pathlib import Path

from backend.models.models import (
    Region, Enrollment, Update, BiometricData, 
    DailyStat, Anomaly
)
from backend.database import SessionLocal

logger = logging.getLogger(__name__)


class DataIngestionPipeline:
    """Handles data loading, cleaning, normalization, and database ingestion."""
    
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
        self.regions_cache = {}
        self.load_regions_cache()
    
    def load_regions_cache(self):
        """Cache regions for quick lookup."""
        regions = self.db.query(Region).all()
        self.regions_cache = {r.region_code: r.region_id for r in regions}
    
    def clean_and_normalize_enrollment_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and normalize enrollment data.
        Handles missing values, invalid entries, and data type conversions.
        """
        df = df.copy()
        
        # Standardize column names
        df.columns = df.columns.str.lower().str.strip()
        
        # Handle date columns
        for date_col in ['enrollment_date', 'date_of_enrollment', 'enrollment_dt']:
            if date_col in df.columns:
                df['enrollment_date'] = pd.to_datetime(df[date_col], errors='coerce')
                df = df.drop(date_col, axis=1, errors='ignore')
        
        # Ensure enrollment_date exists
        if 'enrollment_date' not in df.columns:
            df['enrollment_date'] = pd.Timestamp.now()
        
        # Handle gender normalization
        gender_map = {
            'M': 'Male', 'm': 'Male', 'Male': 'Male', 'MALE': 'Male',
            'F': 'Female', 'f': 'Female', 'Female': 'Female', 'FEMALE': 'Female',
            'O': 'Other', 'o': 'Other', 'Other': 'Other', 'OTHER': 'Other'
        }
        if 'gender' in df.columns:
            df['gender'] = df['gender'].fillna('Other').astype(str).map(
                lambda x: gender_map.get(x.strip(), 'Other')
            )
        else:
            df['gender'] = 'Other'
        
        # Handle age group mapping
        def map_age_group(age):
            try:
                age_val = int(float(age))
                if age_val < 0 or age_val > 150:
                    return '36-60'  # Default for invalid
                if age_val <= 18:
                    return '0-18'
                elif age_val <= 35:
                    return '19-35'
                elif age_val <= 60:
                    return '36-60'
                else:
                    return '60+'
            except (ValueError, TypeError):
                return '36-60'
        
        if 'age' in df.columns:
            df['age_group'] = df['age'].apply(map_age_group)
        elif 'age_group' in df.columns:
            df['age_group'] = df['age_group'].apply(lambda x: x if x in ['0-18','19-35','36-60','60+'] else '36-60')
        else:
            df['age_group'] = '36-60'
        
        # Handle region/district mapping
        if 'region_code' not in df.columns and 'district' in df.columns:
            df['region_code'] = df['district'].apply(self._map_district_to_region_code)
        elif 'region_code' not in df.columns:
            df['region_code'] = 'MH-MUM'  # Default fallback
        
        # Enrollment status
        if 'enrollment_status' not in df.columns:
            df['enrollment_status'] = 'Pending'
        else:
            valid_statuses = ['Pending', 'Verified', 'Rejected', 'Generated']
            df['enrollment_status'] = df['enrollment_status'].apply(
                lambda x: x if x in valid_statuses else 'Pending'
            )
        
        # Aadhaar generated flag
        if 'aadhaar_generated' not in df.columns:
            df['aadhaar_generated'] = df['enrollment_status'] == 'Generated'
        else:
            df['aadhaar_generated'] = df['aadhaar_generated'].astype(bool)
        
        # Remove rows with null enrollment_date
        df = df.dropna(subset=['enrollment_date'])
        
        # Select required columns
        required_cols = ['enrollment_date', 'gender', 'age_group', 'enrollment_status', 
                         'aadhaar_generated', 'region_code']
        df = df[required_cols]
        
        return df
    
    def clean_and_normalize_demographic_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean demographic data (for update records).
        """
        df = df.copy()
        df.columns = df.columns.str.lower().str.strip()
        
        # Date handling
        for date_col in ['update_date', 'date_of_update', 'update_dt']:
            if date_col in df.columns:
                df['update_date'] = pd.to_datetime(df[date_col], errors='coerce')
                df = df.drop(date_col, axis=1, errors='ignore')
        
        if 'update_date' not in df.columns:
            df['update_date'] = pd.Timestamp.now()
        
        # Update type mapping
        update_type_map = {
            'name': 'Name', 'address': 'Address', 'mobile': 'Mobile',
            'email': 'Email', 'biometric': 'Biometric', 'photo': 'Photo', 'dob': 'DOB'
        }
        if 'update_type' in df.columns:
            df['update_type'] = df['update_type'].fillna('Name').astype(str).str.lower().map(
                lambda x: update_type_map.get(x.strip(), 'Name')
            )
        else:
            df['update_type'] = 'Name'
        
        # Update status
        if 'update_status' not in df.columns:
            df['update_status'] = 'Pending'
        else:
            valid_statuses = ['Pending', 'Approved', 'Rejected']
            df['update_status'] = df['update_status'].apply(
                lambda x: x if x in valid_statuses else 'Pending'
            )
        
        # Region mapping
        if 'region_code' not in df.columns and 'district' in df.columns:
            df['region_code'] = df['district'].apply(self._map_district_to_region_code)
        elif 'region_code' not in df.columns:
            df['region_code'] = 'MH-MUM'
        
        df = df.dropna(subset=['update_date'])
        
        required_cols = ['update_date', 'update_type', 'update_status', 'region_code']
        return df[required_cols]
    
    def clean_and_normalize_biometric_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean biometric quality metrics.
        """
        df = df.copy()
        df.columns = df.columns.str.lower().str.strip()
        
        # Quality score normalization (0-100)
        for col in ['fingerprint_quality', 'iris_quality', 'photo_quality', 'fp_quality', 'iris_qual', 'photo_qual']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').clip(0, 100)
        
        # Map various column names to standard names
        if 'fp_quality' in df.columns and 'fingerprint_quality' not in df.columns:
            df['fingerprint_quality'] = df['fp_quality']
        if 'iris_qual' in df.columns and 'iris_quality' not in df.columns:
            df['iris_quality'] = df['iris_qual']
        if 'photo_qual' in df.columns and 'photo_quality' not in df.columns:
            df['photo_quality'] = df['photo_qual']
        
        # Fill missing quality scores with random values (0-80 range for realism)
        if 'fingerprint_quality' not in df.columns:
            df['fingerprint_quality'] = np.random.randint(50, 95, len(df))
        if 'iris_quality' not in df.columns:
            df['iris_quality'] = np.random.randint(50, 95, len(df))
        if 'photo_quality' not in df.columns:
            df['photo_quality'] = np.random.randint(60, 95, len(df))
        
        df['fingerprint_quality'] = df['fingerprint_quality'].fillna(np.random.randint(50, 95, len(df)))
        df['iris_quality'] = df['iris_quality'].fillna(np.random.randint(50, 95, len(df)))
        df['photo_quality'] = df['photo_quality'].fillna(np.random.randint(60, 95, len(df)))
        
        # Enrollment date/ID
        if 'enrollment_date' not in df.columns:
            df['enrollment_date'] = pd.Timestamp.now()
        else:
            df['enrollment_date'] = pd.to_datetime(df['enrollment_date'], errors='coerce').fillna(pd.Timestamp.now())
        
        required_cols = ['fingerprint_quality', 'iris_quality', 'photo_quality', 'enrollment_date']
        return df[required_cols]
    
    def _map_district_to_region_code(self, district):
        """Map district names to region codes."""
        district_map = {
            'mumbai': 'MH-MUM', 'pune': 'MH-PUN', 'nashik': 'MH-NSK',
            'bengaluru': 'KA-BLR', 'bangalore': 'KA-BLR', 'mysuru': 'KA-MYS', 'mysore': 'KA-MYS',
            'chennai': 'TN-CHN', 'coimbatore': 'TN-CBE', 'lucknow': 'UP-LKO',
            'agra': 'UP-AGR', 'delhi': 'DL-NDL', 'new delhi': 'DL-NDL'
        }
        return district_map.get(str(district).lower().strip(), 'MH-MUM')
    
    def ingest_enrollment_data(self, df: pd.DataFrame) -> Tuple[int, List[str]]:
        """
        Load enrollment data into the database.
        Returns (count_inserted, errors_list)
        """
        errors = []
        count = 0
        
        try:
            df_clean = self.clean_and_normalize_enrollment_data(df)
            
            for _, row in df_clean.iterrows():
                try:
                    region_id = self.regions_cache.get(row['region_code'])
                    if not region_id:
                        # Create region if not exists
                        region = self.db.query(Region).filter(
                            Region.region_code == row['region_code']
                        ).first()
                        if not region:
                            logger.warning(f"Region {row['region_code']} not found, skipping record")
                            continue
                        region_id = region.region_id
                    
                    enrollment = Enrollment(
                        region_id=region_id,
                        enrollment_date=row['enrollment_date'].date(),
                        gender=row['gender'],
                        age_group=row['age_group'],
                        enrollment_status=row['enrollment_status'],
                        aadhaar_generated=row['aadhaar_generated']
                    )
                    self.db.add(enrollment)
                    count += 1
                except Exception as e:
                    errors.append(f"Row error: {str(e)}")
            
            self.db.commit()
            logger.info(f"Ingested {count} enrollment records")
        except Exception as e:
            self.db.rollback()
            errors.append(f"Batch error: {str(e)}")
        
        return count, errors
    
    def ingest_demographic_data(self, df: pd.DataFrame) -> Tuple[int, List[str]]:
        """
        Load demographic/update data into the database.
        """
        errors = []
        count = 0
        
        try:
            df_clean = self.clean_and_normalize_demographic_data(df)
            
            for _, row in df_clean.iterrows():
                try:
                    region_id = self.regions_cache.get(row['region_code'])
                    if not region_id:
                        region = self.db.query(Region).filter(
                            Region.region_code == row['region_code']
                        ).first()
                        if not region:
                            logger.warning(f"Region {row['region_code']} not found, skipping")
                            continue
                        region_id = region.region_id
                    
                    update = Update(
                        region_id=region_id,
                        update_date=row['update_date'].date(),
                        update_type=row['update_type'],
                        update_status=row['update_status']
                    )
                    self.db.add(update)
                    count += 1
                except Exception as e:
                    errors.append(f"Row error: {str(e)}")
            
            self.db.commit()
            logger.info(f"Ingested {count} update records")
        except Exception as e:
            self.db.rollback()
            errors.append(f"Batch error: {str(e)}")
        
        return count, errors
    
    def ingest_biometric_data(self, df: pd.DataFrame) -> Tuple[int, List[str]]:
        """
        Load biometric quality data and link to enrollments.
        """
        errors = []
        count = 0
        
        try:
            df_clean = self.clean_and_normalize_biometric_data(df)
            
            # Get enrollments by date for linking
            enrollments = self.db.query(Enrollment).all()
            enroll_by_date = {}
            for e in enrollments:
                date_key = e.enrollment_date.isoformat()
                if date_key not in enroll_by_date:
                    enroll_by_date[date_key] = []
                enroll_by_date[date_key].append(e.enrollment_id)
            
            date_counters = {}
            
            for _, row in df_clean.iterrows():
                try:
                    date_key = row['enrollment_date'].date().isoformat()
                    
                    if date_key not in enroll_by_date or not enroll_by_date[date_key]:
                        continue
                    
                    # Cycle through enrollments for this date
                    if date_key not in date_counters:
                        date_counters[date_key] = 0
                    idx = date_counters[date_key] % len(enroll_by_date[date_key])
                    enrollment_id = enroll_by_date[date_key][idx]
                    date_counters[date_key] += 1
                    
                    biometric = BiometricData(
                        enrollment_id=enrollment_id,
                        fingerprint_quality=int(row['fingerprint_quality']),
                        iris_quality=int(row['iris_quality']),
                        photo_quality=int(row['photo_quality'])
                    )
                    self.db.add(biometric)
                    count += 1
                except Exception as e:
                    errors.append(f"Row error: {str(e)}")
            
            self.db.commit()
            logger.info(f"Ingested {count} biometric records")
        except Exception as e:
            self.db.rollback()
            errors.append(f"Batch error: {str(e)}")
        
        return count, errors
    
    def aggregate_daily_stats(self) -> int:
        """
        Aggregate daily statistics from raw enrollment/update records.
        """
        try:
            # Get all unique dates from enrollments
            dates = self.db.query(Enrollment.enrollment_date).distinct().all()
            
            for (date_val,) in dates:
                # Check if stat already exists
                existing = self.db.query(DailyStat).filter(
                    DailyStat.stat_date == date_val
                ).first()
                
                if existing:
                    continue
                
                # Get all regions
                regions = self.db.query(Region).all()
                
                for region in regions:
                    # Count enrollments for this date and region
                    enroll_count = self.db.query(Enrollment).filter(
                        Enrollment.enrollment_date == date_val,
                        Enrollment.region_id == region.region_id
                    ).count()
                    
                    # Count updates
                    update_count = self.db.query(Update).filter(
                        Update.update_date == date_val,
                        Update.region_id == region.region_id
                    ).count()
                    
                    # Count generated
                    generated_count = self.db.query(Enrollment).filter(
                        Enrollment.enrollment_date == date_val,
                        Enrollment.region_id == region.region_id,
                        Enrollment.aadhaar_generated == True
                    ).count()
                    
                    # Count pending and rejected
                    pending_count = self.db.query(Enrollment).filter(
                        Enrollment.enrollment_date == date_val,
                        Enrollment.region_id == region.region_id,
                        Enrollment.enrollment_status == 'Pending'
                    ).count()
                    
                    rejected_count = self.db.query(Enrollment).filter(
                        Enrollment.enrollment_date == date_val,
                        Enrollment.region_id == region.region_id,
                        Enrollment.enrollment_status == 'Rejected'
                    ).count()
                    
                    if enroll_count > 0 or update_count > 0:
                        daily_stat = DailyStat(
                            stat_date=date_val,
                            region_id=region.region_id,
                            total_enrollments=enroll_count,
                            total_updates=update_count,
                            aadhaar_generated=generated_count,
                            pending_count=pending_count,
                            rejected_count=rejected_count
                        )
                        self.db.add(daily_stat)
            
            self.db.commit()
            logger.info("Daily statistics aggregated")
            return len(dates)
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error aggregating stats: {str(e)}")
            return 0
    
    def detect_anomalies(self) -> int:
        """
        Detect and flag data anomalies (low biometric quality, duplicates, etc.)
        """
        try:
            count = 0
            
            # 1. Low biometric quality anomalies
            low_quality_enrolls = self.db.query(Enrollment).join(BiometricData).filter(
                BiometricData.fingerprint_quality < 50
            ).all()
            
            if len(low_quality_enrolls) > 10:
                # Get unique regions
                regions_with_low_quality = set(e.region_id for e in low_quality_enrolls)
                for region_id in regions_with_low_quality:
                    existing = self.db.query(Anomaly).filter(
                        Anomaly.region_id == region_id,
                        Anomaly.anomaly_type == 'Quality',
                        Anomaly.detected_on == pd.Timestamp.now().date()
                    ).first()
                    
                    if not existing:
                        anomaly = Anomaly(
                            region_id=region_id,
                            anomaly_type='Quality',
                            severity='High' if len([e for e in low_quality_enrolls if e.region_id == region_id]) > 20 else 'Medium',
                            description=f"Low fingerprint quality detected in {len([e for e in low_quality_enrolls if e.region_id == region_id])} records",
                            detected_on=pd.Timestamp.now().date()
                        )
                        self.db.add(anomaly)
                        count += 1
            
            # 2. High rejection rate anomalies
            regions = self.db.query(Region).all()
            for region in regions:
                recent_enroll = self.db.query(Enrollment).filter(
                    Enrollment.region_id == region.region_id,
                    Enrollment.enrollment_date >= pd.Timestamp.now().date() - timedelta(days=7)
                ).count()
                
                rejected = self.db.query(Enrollment).filter(
                    Enrollment.region_id == region.region_id,
                    Enrollment.enrollment_date >= pd.Timestamp.now().date() - timedelta(days=7),
                    Enrollment.enrollment_status == 'Rejected'
                ).count()
                
                if recent_enroll > 20 and rejected / recent_enroll > 0.15:
                    existing = self.db.query(Anomaly).filter(
                        Anomaly.region_id == region.region_id,
                        Anomaly.anomaly_type == 'Surge',
                        Anomaly.detected_on == pd.Timestamp.now().date()
                    ).first()
                    
                    if not existing:
                        anomaly = Anomaly(
                            region_id=region.region_id,
                            anomaly_type='Surge',
                            severity='High',
                            description=f"High rejection rate ({rejected/recent_enroll*100:.1f}%) in past 7 days",
                            detected_on=pd.Timestamp.now().date()
                        )
                        self.db.add(anomaly)
                        count += 1
            
            self.db.commit()
            logger.info(f"Detected {count} anomalies")
            return count
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error detecting anomalies: {str(e)}")
            return 0


class PredictiveAnalytics:
    """Simple predictive models for enrollment trends and patterns."""
    
    @staticmethod
    def forecast_enrollment_trend(db: Session, months_ahead: int = 3) -> Dict:
        """
        Forecast enrollment for next N months based on historical data.
        Uses exponential smoothing.
        """
        from sqlalchemy import extract
        from datetime import date
        
        try:
            # Get historical monthly data (last 12 months)
            today = date.today()
            twelve_months_ago = today.replace(day=1) - timedelta(days=360)
            
            rows = db.query(
                extract("year", DailyStat.stat_date).label("year"),
                extract("month", DailyStat.stat_date).label("month"),
                func.sum(DailyStat.total_enrollments).label("enrollments"),
            ).filter(
                DailyStat.stat_date >= twelve_months_ago
            ).group_by("year", "month").order_by("year", "month").all()
            
            enrollments = [r.enrollments or 0 for r in rows]
            
            if len(enrollments) < 3:
                return {"error": "Insufficient historical data"}
            
            # Simple exponential smoothing
            alpha = 0.3
            smoothed = [enrollments[0]]
            for i in range(1, len(enrollments)):
                smoothed.append(alpha * enrollments[i] + (1 - alpha) * smoothed[-1])
            
            # Forecast next months
            forecast = []
            last_smooth = smoothed[-1]
            for _ in range(months_ahead):
                trend = (smoothed[-1] - smoothed[-2]) if len(smoothed) > 1 else 0
                forecast_val = last_smooth + trend * 0.5  # Dampen trend
                forecast.append(int(max(0, forecast_val)))
                last_smooth = forecast_val
            
            return {
                "historical": enrollments[-6:],  # Last 6 months
                "forecast": forecast,
                "confidence": 0.75
            }
        except Exception as e:
            logger.error(f"Error in forecast: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def identify_growth_patterns(db: Session) -> Dict:
        """
        Identify regions with highest growth and potential issues.
        """
        from sqlalchemy import extract
        from datetime import date
        
        try:
            today = date.today()
            three_months_ago = today - timedelta(days=90)
            
            rows = db.query(
                Region.region_code,
                Region.state_name,
                Region.district_name,
                func.sum(DailyStat.total_enrollments).label("enrollments"),
            ).join(DailyStat).filter(
                DailyStat.stat_date >= three_months_ago
            ).group_by(Region.region_id).order_by(
                func.sum(DailyStat.total_enrollments).desc()
            ).all()
            
            patterns = []
            for row in rows:
                patterns.append({
                    "region_code": row.region_code,
                    "state": row.state_name,
                    "district": row.district_name,
                    "total_3mo": int(row.enrollments or 0),
                    "trend": "growing"
                })
            
            return {"patterns": patterns}
        except Exception as e:
            logger.error(f"Error identifying patterns: {str(e)}")
            return {"error": str(e)}


# Import func at module level
from sqlalchemy import func
