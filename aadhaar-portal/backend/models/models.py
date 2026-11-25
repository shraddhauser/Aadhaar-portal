"""
backend/models/models.py
SQLAlchemy ORM models mirroring the database schema.
"""

from sqlalchemy import (
    Column, Integer, String, Enum, Boolean,
    Date, Text, SmallInteger, ForeignKey, UniqueConstraint, DateTime
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base


class Region(Base):
    __tablename__ = "regions"

    region_id     = Column(Integer, primary_key=True, autoincrement=True)
    state_name    = Column(String(100), nullable=False)
    district_name = Column(String(100), nullable=False)
    region_code   = Column(String(20), unique=True, nullable=False)
    created_at    = Column(DateTime, server_default=func.now())

    enrollments   = relationship("Enrollment", back_populates="region")
    updates       = relationship("Update", back_populates="region")
    anomalies     = relationship("Anomaly", back_populates="region")
    daily_stats   = relationship("DailyStat", back_populates="region")


class Enrollment(Base):
    __tablename__ = "enrollments"

    enrollment_id     = Column(Integer, primary_key=True, autoincrement=True)
    region_id         = Column(Integer, ForeignKey("regions.region_id"), nullable=False)
    enrollment_date   = Column(Date, nullable=False)
    gender            = Column(Enum("Male", "Female", "Other"), nullable=False)
    age_group         = Column(Enum("0-18", "19-35", "36-60", "60+"), nullable=False)
    enrollment_status = Column(
        Enum("Pending", "Verified", "Rejected", "Generated"),
        nullable=False, default="Pending"
    )
    aadhaar_generated = Column(Boolean, default=False)
    created_at        = Column(DateTime, server_default=func.now())

    region            = relationship("Region", back_populates="enrollments")
    biometric         = relationship("BiometricData", back_populates="enrollment", uselist=False)


class Update(Base):
    __tablename__ = "updates"

    update_id     = Column(Integer, primary_key=True, autoincrement=True)
    region_id     = Column(Integer, ForeignKey("regions.region_id"), nullable=False)
    update_date   = Column(Date, nullable=False)
    update_type   = Column(
        Enum("Name", "Address", "Mobile", "Email", "Biometric", "Photo", "DOB"),
        nullable=False
    )
    update_status = Column(
        Enum("Pending", "Approved", "Rejected"),
        nullable=False, default="Pending"
    )
    created_at    = Column(DateTime, server_default=func.now())

    region        = relationship("Region", back_populates="updates")


class BiometricData(Base):
    __tablename__ = "biometric_data"

    biometric_id        = Column(Integer, primary_key=True, autoincrement=True)
    enrollment_id       = Column(Integer, ForeignKey("enrollments.enrollment_id"), nullable=False)
    fingerprint_quality = Column(SmallInteger)
    iris_quality        = Column(SmallInteger)
    photo_quality       = Column(SmallInteger)
    captured_at         = Column(DateTime, server_default=func.now())

    enrollment          = relationship("Enrollment", back_populates="biometric")


class Anomaly(Base):
    __tablename__ = "anomalies"

    anomaly_id   = Column(Integer, primary_key=True, autoincrement=True)
    region_id    = Column(Integer, ForeignKey("regions.region_id"), nullable=False)
    anomaly_type = Column(Enum("Duplicate", "Quality", "Surge", "Drop", "Mismatch"), nullable=False)
    severity     = Column(Enum("Low", "Medium", "High", "Critical"), nullable=False)
    description  = Column(Text)
    detected_on  = Column(Date, nullable=False)
    resolved     = Column(Boolean, default=False)
    created_at   = Column(DateTime, server_default=func.now())

    region       = relationship("Region", back_populates="anomalies")


class DailyStat(Base):
    __tablename__ = "daily_stats"

    stat_id           = Column(Integer, primary_key=True, autoincrement=True)
    stat_date         = Column(Date, nullable=False)
    region_id         = Column(Integer, ForeignKey("regions.region_id"), nullable=False)
    total_enrollments = Column(Integer, default=0)
    total_updates     = Column(Integer, default=0)
    aadhaar_generated = Column(Integer, default=0)
    pending_count     = Column(Integer, default=0)
    rejected_count    = Column(Integer, default=0)

    __table_args__ = (UniqueConstraint("stat_date", "region_id"),)

    region            = relationship("Region", back_populates="daily_stats")


class AdminUser(Base):
    __tablename__ = "admin_users"

    admin_id      = Column(Integer, primary_key=True, autoincrement=True)
    username      = Column(String(80), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name     = Column(String(150))
    role          = Column(Enum("SuperAdmin", "Analyst", "Viewer"), default="Viewer")
    last_login    = Column(DateTime)
    created_at    = Column(DateTime, server_default=func.now())
