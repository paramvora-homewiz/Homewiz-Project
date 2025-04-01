from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..services import analytics_service
from ..db.connection import get_db

router = APIRouter()

@router.get("/analytics/occupancy", response_model=Dict[str, Any])
def get_occupancy_rate(
    building_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get current occupancy rate metrics.
    """
    return analytics_service.get_occupancy_rate(db, building_id)

@router.get("/analytics/financial", response_model=Dict[str, Any])
def get_financial_metrics(
    building_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """
    Get financial metrics like total revenue, average rent, etc.
    """
    return analytics_service.get_financial_metrics(db, building_id, start_date, end_date)

@router.get("/analytics/leads", response_model=Dict[str, Any])
def get_lead_conversion_metrics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """
    Get lead conversion metrics.
    """
    return analytics_service.get_lead_conversion_metrics(db, start_date, end_date)

@router.get("/analytics/maintenance", response_model=Dict[str, Any])
def get_maintenance_metrics(
    building_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """
    Get maintenance request metrics.
    """
    return analytics_service.get_maintenance_metrics(db, building_id, start_date, end_date)

@router.get("/analytics/rooms", response_model=Dict[str, Any])
def get_room_performance_metrics(
    building_id: Optional[str] = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get room performance metrics.
    """
    return analytics_service.get_room_performance_metrics(db, building_id, limit)

@router.get("/analytics/tenants", response_model=Dict[str, Any])
def get_tenant_metrics(
    building_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get tenant metrics.
    """
    return analytics_service.get_tenant_metrics(db, building_id)

@router.get("/analytics/dashboard", response_model=Dict[str, Any])
def get_dashboard_metrics(
    building_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get a comprehensive dashboard with multiple metrics.
    """
    return analytics_service.get_dashboard_metrics(db, building_id)

@router.post("/analytics/property-comparison", response_model=Dict[str, Any])
def compare_properties(building_ids: List[str], db: Session = Depends(get_db)):
    """
    Compare metrics across multiple properties.
    """
    return analytics_service.get_property_comparison(db, building_ids)

@router.get("/analytics/lead-sources", response_model=Dict[str, Any])
def analyze_lead_sources(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """
    Analyze lead sources to determine which are most effective.
    """
    return analytics_service.get_lead_source_analysis(db, start_date, end_date)

@router.get("/analytics/occupancy-history", response_model=Dict[str, Any])
def get_occupancy_history(
    building_id: Optional[str] = None,
    months: int = 12,
    db: Session = Depends(get_db)
):
    """
    Get historical occupancy data for trend analysis.
    """
    return analytics_service.get_occupancy_history(db, building_id, months)