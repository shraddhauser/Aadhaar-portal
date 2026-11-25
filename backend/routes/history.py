"""
backend/routes/history.py
Historical trend analysis endpoints.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import date

from backend.database import get_db
from backend.models.models import DailyStat, Enrollment, Update, Region
from backend.routes.auth import get_current_admin

router = APIRouter()


@router.get("/monthly-trend")
def monthly_trend(
    year: int = Query(default=2024, ge=2010, le=2100),
    region_code: str | None = Query(None),
    db: Session = Depends(get_db),
    _: object = Depends(get_current_admin),
):
    """
    Monthly enrollment and update counts for a given year.
    Returns 12 data points suitable for a line/bar chart.
    """
    q = db.query(
        extract("month", DailyStat.stat_date).label("month"),
        func.sum(DailyStat.total_enrollments).label("enrollments"),
        func.sum(DailyStat.total_updates).label("updates"),
        func.sum(DailyStat.aadhaar_generated).label("generated"),
    ).filter(extract("year", DailyStat.stat_date) == year)

    if region_code:
        region = db.query(Region).filter(Region.region_code == region_code).first()
        if region:
            q = q.filter(DailyStat.region_id == region.region_id)

    rows = q.group_by("month").order_by("month").all()
    return [
        {
            "month":       int(r.month),
            "enrollments": int(r.enrollments or 0),
            "updates":     int(r.updates     or 0),
            "generated":   int(r.generated   or 0),
        }
        for r in rows
    ]


@router.get("/regional-comparison")
def regional_comparison(
    start_date: date = Query(default=date(2024, 1, 1)),
    end_date: date   = Query(default=date(2024, 12, 31)),
    db: Session = Depends(get_db),
    _: object = Depends(get_current_admin),
):
    """
    Total enrollments per state/district within a date range.
    Used for map/heatmap and bar chart comparisons.
    """
    rows = db.query(
        Region.state_name,
        Region.district_name,
        Region.region_code,
        func.sum(DailyStat.total_enrollments).label("enrollments"),
        func.sum(DailyStat.total_updates).label("updates"),
    ).join(DailyStat, DailyStat.region_id == Region.region_id
    ).filter(DailyStat.stat_date.between(start_date, end_date)
    ).group_by(Region.region_id
    ).order_by(func.sum(DailyStat.total_enrollments).desc()
    ).all()

    return [
        {
            "state":       r.state_name,
            "district":    r.district_name,
            "region_code": r.region_code,
            "enrollments": int(r.enrollments or 0),
            "updates":     int(r.updates     or 0),
        }
        for r in rows
    ]


@router.get("/yearly-growth")
def yearly_growth(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_admin),
):
    """Year-over-year enrollment growth totals."""
    rows = db.query(
        extract("year", DailyStat.stat_date).label("year"),
        func.sum(DailyStat.total_enrollments).label("enrollments"),
        func.sum(DailyStat.aadhaar_generated).label("generated"),
    ).group_by("year").order_by("year").all()

    return [
        {
            "year":        int(r.year),
            "enrollments": int(r.enrollments or 0),
            "generated":   int(r.generated   or 0),
        }
        for r in rows
    ]


@router.get("/update-history")
def update_history(
    start_date: date = Query(default=date(2024, 1, 1)),
    end_date: date   = Query(default=date(2024, 12, 31)),
    db: Session = Depends(get_db),
    _: object = Depends(get_current_admin),
):
    """Update counts grouped by type within a date range."""
    rows = db.query(
        Update.update_type,
        Update.update_status,
        func.count(Update.update_id).label("count"),
    ).filter(Update.update_date.between(start_date, end_date)
    ).group_by(Update.update_type, Update.update_status).all()

    return [
        {"type": r.update_type, "status": r.update_status, "count": r.count}
        for r in rows
    ]
