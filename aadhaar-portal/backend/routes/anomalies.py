"""
backend/routes/anomalies.py
Anomaly detection and listing endpoints.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta

from backend.database import get_db
from backend.models.models import Anomaly, DailyStat, Region
from backend.routes.auth import get_current_admin

router = APIRouter()


@router.get("/list")
def list_anomalies(
    resolved: bool | None = Query(None, description="Filter by resolved status"),
    severity: str | None  = Query(None, description="Low | Medium | High | Critical"),
    db: Session = Depends(get_db),
    _: object = Depends(get_current_admin),
):
    """Return all anomaly records, optionally filtered."""
    q = db.query(Anomaly)
    if resolved is not None:
        q = q.filter(Anomaly.resolved == resolved)
    if severity:
        q = q.filter(Anomaly.severity == severity)
    rows = q.order_by(Anomaly.detected_on.desc()).limit(200).all()
    return [
        {
            "anomaly_id":   r.anomaly_id,
            "anomaly_type": r.anomaly_type,
            "severity":     r.severity,
            "description":  r.description,
            "detected_on":  str(r.detected_on),
            "resolved":     r.resolved,
            "region_code":  r.region.region_code if r.region else None,
        }
        for r in rows
    ]


@router.get("/detect-surges")
def detect_surges(
    threshold_pct: float = Query(default=50.0, ge=10, le=500),
    db: Session = Depends(get_db),
    _: object = Depends(get_current_admin),
):
    """
    Detect enrollment surges: regions where today's count is
    more than `threshold_pct`% above their 7-day average.
    """
    today   = date.today()
    week_ago = today - timedelta(days=7)

    # 7-day averages per region
    avg_q = db.query(
        DailyStat.region_id,
        func.avg(DailyStat.total_enrollments).label("avg_7d"),
    ).filter(
        DailyStat.stat_date.between(week_ago, today - timedelta(days=1))
    ).group_by(DailyStat.region_id).subquery()

    # Today's counts
    today_q = db.query(
        DailyStat.region_id,
        DailyStat.total_enrollments.label("today_count"),
    ).filter(DailyStat.stat_date == today).subquery()

    rows = db.query(
        Region.region_code,
        Region.district_name,
        Region.state_name,
        today_q.c.today_count,
        avg_q.c.avg_7d,
    ).join(today_q, today_q.c.region_id == Region.region_id
    ).join(avg_q,   avg_q.c.region_id   == Region.region_id
    ).all()

    surges = [
        {
            "region_code": r.region_code,
            "district":    r.district_name,
            "state":       r.state_name,
            "today":       r.today_count,
            "avg_7d":      round(float(r.avg_7d), 1),
            "pct_change":  round(((r.today_count - float(r.avg_7d)) / float(r.avg_7d)) * 100, 1)
                           if r.avg_7d else 0,
        }
        for r in rows
        if r.avg_7d and ((r.today_count - float(r.avg_7d)) / float(r.avg_7d)) * 100 >= threshold_pct
    ]
    return {"threshold_pct": threshold_pct, "surges": surges}
