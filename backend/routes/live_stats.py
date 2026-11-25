"""
backend/routes/live_stats.py
Real-time enrolment and update metrics endpoint.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
from datetime import date, timedelta

from backend.database import get_db
from backend.models.models import Enrollment, Update, DailyStat, Region
from backend.routes.auth import get_current_admin

router = APIRouter()


@router.get("/summary")
def live_summary(
    region_code: str | None = Query(None, description="Filter by region code"),
    db: Session = Depends(get_db),
    _: object = Depends(get_current_admin),
):
    """
    Returns high-level KPI cards:
    - total enrollments today
    - total updates today
    - Aadhaar IDs generated today
    - pending count
    """
    today = date.today()
    q = db.query(DailyStat)

    if region_code:
        region = db.query(Region).filter(Region.region_code == region_code).first()
        if region:
            q = q.filter(DailyStat.region_id == region.region_id)

    # Try today first; if no data, fall back to the most recent date with data
    target_date = today
    check = q.filter(DailyStat.stat_date == today).with_entities(
        func.count(DailyStat.stat_id)
    ).scalar()

    if not check:
        latest = q.with_entities(
            func.max(DailyStat.stat_date)
        ).scalar()
        if latest:
            target_date = latest

    row = q.filter(DailyStat.stat_date == target_date).with_entities(
        func.sum(DailyStat.total_enrollments).label("enrollments"),
        func.sum(DailyStat.total_updates).label("updates"),
        func.sum(DailyStat.aadhaar_generated).label("generated"),
        func.sum(DailyStat.pending_count).label("pending"),
        func.sum(DailyStat.rejected_count).label("rejected"),
    ).one()

    return {
        "date":        str(target_date),
        "enrollments": int(row.enrollments or 0),
        "updates":     int(row.updates     or 0),
        "generated":   int(row.generated   or 0),
        "pending":     int(row.pending     or 0),
        "rejected":    int(row.rejected    or 0),
    }


@router.get("/gender-split")
def gender_split(
    region_code: str | None = Query(None),
    days: int | None = Query(30, ge=0, description='Number of days back to include; 0 = all time'),
    db: Session = Depends(get_db),
    _: object = Depends(get_current_admin),
):
    """Gender distribution of enrollments in the last 30 days."""
    # Determine time window
    q = db.query(
        Enrollment.gender,
        func.count(Enrollment.enrollment_id).label("count"),
    )
    if days and days > 0:
        since = date.today() - timedelta(days=days)
        q = q.filter(Enrollment.enrollment_date >= since)

    if region_code:
        region = db.query(Region).filter(Region.region_code == region_code).first()
        if region:
            q = q.filter(Enrollment.region_id == region.region_id)

    rows = q.group_by(Enrollment.gender).all()
    return [{"gender": r.gender, "count": r.count} for r in rows]


@router.get("/age-split")
def age_split(
    region_code: str | None = Query(None),
    days: int | None = Query(30, ge=0, description='Number of days back to include; 0 = all time'),
    db: Session = Depends(get_db),
    _: object = Depends(get_current_admin),
):
    """Age-group distribution of enrollments in the last 30 days."""
    q = db.query(
        Enrollment.age_group,
        func.count(Enrollment.enrollment_id).label("count"),
    )
    if days and days > 0:
        since = date.today() - timedelta(days=days)
        q = q.filter(Enrollment.enrollment_date >= since)

    if region_code:
        region = db.query(Region).filter(Region.region_code == region_code).first()
        if region:
            q = q.filter(Enrollment.region_id == region.region_id)

    rows = q.group_by(Enrollment.age_group).all()
    return [{"age_group": r.age_group, "count": r.count} for r in rows]


@router.get("/status-breakdown")
def status_breakdown(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_admin),
):
    """Enrollment status breakdown (all time)."""
    rows = db.query(
        Enrollment.enrollment_status,
        func.count(Enrollment.enrollment_id).label("count"),
    ).group_by(Enrollment.enrollment_status).all()
    return [{"status": r.enrollment_status, "count": r.count} for r in rows]


@router.get("/update-types")
def update_types(
    days: int | None = Query(30, ge=0, description='Number of days back to include; 0 = all time'),
    db: Session = Depends(get_db),
    _: object = Depends(get_current_admin),
):
    """Update request breakdown by type (last 30 days)."""
    q = db.query(
        Update.update_type,
        func.count(Update.update_id).label("count"),
    )
    if days and days > 0:
        since = date.today() - timedelta(days=days)
        q = q.filter(Update.update_date >= since)
    rows = q.group_by(Update.update_type).all()
    return [{"type": r.update_type, "count": r.count} for r in rows]


@router.get("/regions")
def all_regions(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_admin),
):
    """List all available regions for filter dropdowns."""
    rows = db.query(Region).order_by(Region.state_name, Region.district_name).all()
    return [
        {
            "region_id":    r.region_id,
            "region_code":  r.region_code,
            "state_name":   r.state_name,
            "district_name": r.district_name,
        }
        for r in rows
    ]
