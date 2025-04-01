from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
from sqlalchemy import func, desc, and_, or_, case, cast, Float
from sqlalchemy.orm import Session

from ..db import models

def get_occupancy_rate(
    db: Session,
    building_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculates the current occupancy rate.
    Can be filtered by building_id.
    """
    # Base query for all rooms
    rooms_query = db.query(models.Room)
    active_rooms_query = db.query(models.Room).filter(models.Room.ready_to_rent == True)
    
    # Filter by building if provided
    if building_id:
        rooms_query = rooms_query.filter(models.Room.building_id == building_id)
        active_rooms_query = active_rooms_query.filter(models.Room.building_id == building_id)
    
    # Get total rooms and occupied rooms
    total_rooms = rooms_query.count()
    available_rooms = active_rooms_query.filter(models.Room.status == "AVAILABLE").count()
    occupied_rooms = active_rooms_query.filter(models.Room.status != "AVAILABLE").count()
    
    # Calculate occupancy percentage
    occupancy_rate = 0
    if total_rooms > 0:
        occupancy_rate = (occupied_rooms / total_rooms) * 100
    
    return {
        "total_rooms": total_rooms,
        "available_rooms": available_rooms,
        "occupied_rooms": occupied_rooms,
        "occupancy_rate": round(occupancy_rate, 2)
    }

def get_financial_metrics(
    db: Session,
    building_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Calculates financial metrics like total revenue, average rent, etc.
    """
    # Default to the current month if dates aren't provided
    if not start_date:
        start_date = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if not end_date:
        next_month = start_date.replace(day=28) + timedelta(days=4)
        end_date = next_month.replace(day=1) - timedelta(days=1)
    
    # Base query for occupied rooms
    rooms_query = db.query(models.Room).filter(
        models.Room.status != "AVAILABLE",
        models.Room.ready_to_rent == True
    )
    
    # Filter by building if provided
    if building_id:
        rooms_query = rooms_query.filter(models.Room.building_id == building_id)
    
    # Get financial metrics
    occupied_rooms = rooms_query.all()
    
    # Calculate total private room rent and shared room rent
    total_private_rent = sum(room.private_room_rent for room in occupied_rooms if room.private_room_rent)
    total_shared_rent = sum(room.shared_room_rent_2 for room in occupied_rooms if room.shared_room_rent_2)
    
    # Calculate average rents
    avg_private_rent = 0
    if occupied_rooms:
        private_rents = [room.private_room_rent for room in occupied_rooms if room.private_room_rent]
        if private_rents:
            avg_private_rent = sum(private_rents) / len(private_rents)
    
    avg_shared_rent = 0
    if occupied_rooms:
        shared_rents = [room.shared_room_rent_2 for room in occupied_rooms if room.shared_room_rent_2]
        if shared_rents:
            avg_shared_rent = sum(shared_rents) / len(shared_rents)
    
    # Estimate monthly revenue based on current occupancy
    estimated_monthly_revenue = total_private_rent + total_shared_rent
    
    return {
        "occupied_room_count": len(occupied_rooms),
        "total_private_rent": round(total_private_rent, 2),
        "total_shared_rent": round(total_shared_rent, 2),
        "avg_private_rent": round(avg_private_rent, 2),
        "avg_shared_rent": round(avg_shared_rent, 2),
        "estimated_monthly_revenue": round(estimated_monthly_revenue, 2),
        "period_start": start_date.strftime("%Y-%m-%d"),
        "period_end": end_date.strftime("%Y-%m-%d")
    }

def get_lead_conversion_metrics(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Calculates lead conversion metrics.
    """
    # Default to the past 30 days if dates aren't provided
    if not start_date:
        start_date = datetime.now() - timedelta(days=30)
    if not end_date:
        end_date = datetime.now()
    
    # Query leads created in the date range
    total_leads = db.query(models.Lead).filter(
        models.Lead.created_at >= start_date,
        models.Lead.created_at <= end_date
    ).count()
    
    # Query leads by status
    leads_by_status = {}
    statuses = ["EXPLORING", "SHOWING_SCHEDULED", "APPLICATION_STARTED", "APPLICATION_SUBMITTED", "LEASE_REQUESTED", "LEASE_SIGNED", "MOVED_IN", "DECLINED"]
    
    for status in statuses:
        count = db.query(models.Lead).filter(
            models.Lead.created_at >= start_date,
            models.Lead.created_at <= end_date,
            models.Lead.status == status
        ).count()
        leads_by_status[status] = count
    
    # Calculate conversion rates
    conversion_rates = {}
    if total_leads > 0:
        for status in statuses:
            conversion_rates[status] = round((leads_by_status[status] / total_leads) * 100, 2)
    
    # Calculate overall conversion rate (leads that moved in)
    overall_conversion_rate = 0
    if total_leads > 0 and "MOVED_IN" in leads_by_status:
        overall_conversion_rate = round((leads_by_status["MOVED_IN"] / total_leads) * 100, 2)
    
    return {
        "total_leads": total_leads,
        "leads_by_status": leads_by_status,
        "conversion_rates": conversion_rates,
        "overall_conversion_rate": overall_conversion_rate,
        "period_start": start_date.strftime("%Y-%m-%d"),
        "period_end": end_date.strftime("%Y-%m-%d")
    }

def get_maintenance_metrics(
    db: Session,
    building_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Calculates maintenance request metrics.
    """
    # Default to the past 30 days if dates aren't provided
    if not start_date:
        start_date = datetime.now() - timedelta(days=30)
    if not end_date:
        end_date = datetime.now()
    
    # Base query for maintenance requests
    requests_query = db.query(models.MaintenanceRequest).filter(
        models.MaintenanceRequest.created_at >= start_date,
        models.MaintenanceRequest.created_at <= end_date
    )
    
    # Filter by building if provided
    if building_id:
        requests_query = requests_query.filter(models.MaintenanceRequest.building_id == building_id)
    
    # Get total requests
    total_requests = requests_query.count()
    
    # Query requests by status
    requests_by_status = {}
    statuses = ["PENDING", "ASSIGNED", "IN_PROGRESS", "COMPLETED", "CANCELLED"]
    
    for status in statuses:
        count = requests_query.filter(models.MaintenanceRequest.status == status).count()
        requests_by_status[status] = count
    
    # Query requests by priority
    requests_by_priority = {}
    priorities = ["LOW", "MEDIUM", "HIGH", "EMERGENCY"]
    
    for priority in priorities:
        count = requests_query.filter(models.MaintenanceRequest.priority == priority).count()
        requests_by_priority[priority] = count
    
    # Calculate average resolution time for completed requests
    avg_resolution_time = None
    completed_requests = requests_query.filter(
        models.MaintenanceRequest.status == "COMPLETED",
        models.MaintenanceRequest.resolved_at.isnot(None)
    ).all()
    
    if completed_requests:
        resolution_times = []
        for request in completed_requests:
            if request.created_at and request.resolved_at:
                delta = request.resolved_at - request.created_at
                resolution_times.append(delta.total_seconds() / 3600)  # Convert to hours
        
        if resolution_times:
            avg_resolution_time = sum(resolution_times) / len(resolution_times)
    
    return {
        "total_requests": total_requests,
        "requests_by_status": requests_by_status,
        "requests_by_priority": requests_by_priority,
        "avg_resolution_time_hours": round(avg_resolution_time, 2) if avg_resolution_time else None,
        "period_start": start_date.strftime("%Y-%m-%d"),
        "period_end": end_date.strftime("%Y-%m-%d")
    }

def get_room_performance_metrics(
    db: Session,
    building_id: Optional[str] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Analyzes room performance to identify top performing and underperforming rooms.
    """
    # Base query for all rooms
    rooms_query = db.query(models.Room)
    
    # Filter by building if provided
    if building_id:
        rooms_query = rooms_query.filter(models.Room.building_id == building_id)
    
    # Get all active rooms
    active_rooms = rooms_query.filter(models.Room.ready_to_rent == True).all()
    
    # Calculate metrics for each room
    room_metrics = []
    for room in active_rooms:
        # Calculate occupancy duration
        occupancy_duration = 0
        if room.booked_from and room.booked_till:
            delta = room.booked_till - room.booked_from
            occupancy_duration = delta.days
        
        # Calculate revenue
        revenue = 0
        if room.private_room_rent:
            revenue = room.private_room_rent * (occupancy_duration / 30)  # Approximate monthly revenue
        
        room_metrics.append({
            "room_id": room.room_id,
            "room_number": room.room_number,
            "building_id": room.building_id,
            "status": room.status,
            "private_room_rent": room.private_room_rent,
            "shared_room_rent_2": room.shared_room_rent_2,
            "occupancy_duration_days": occupancy_duration,
            "estimated_revenue": round(revenue, 2)
        })
    
    # Sort by estimated revenue (descending)
    sorted_metrics = sorted(room_metrics, key=lambda x: x["estimated_revenue"], reverse=True)
    
    # Get top and bottom performing rooms
    top_performing = sorted_metrics[:limit]
    bottom_performing = sorted_metrics[-limit:] if len(sorted_metrics) >= limit else []
    
    return {
        "total_rooms": len(active_rooms),
        "top_performing_rooms": top_performing,
        "bottom_performing_rooms": bottom_performing
    }

def get_tenant_metrics(
    db: Session,
    building_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyzes tenant data for insights.
    """
    # Base query for all active tenants
    tenants_query = db.query(models.Tenant).filter(models.Tenant.status == "ACTIVE")
    
    # Filter by building if provided
    if building_id:
        tenants_query = tenants_query.filter(models.Tenant.building_id == building_id)
    
    # Get all active tenants
    active_tenants = tenants_query.all()
    
    # Calculate lease duration for each tenant
    lease_durations = []
    for tenant in active_tenants:
        if tenant.lease_start_date and tenant.lease_end_date:
            delta = tenant.lease_end_date - tenant.lease_start_date
            lease_durations.append(delta.days)
    
    # Calculate average lease duration
    avg_lease_duration = 0
    if lease_durations:
        avg_lease_duration = sum(lease_durations) / len(lease_durations)
    
    # Count payment statuses
    payment_statuses = {}
    for tenant in active_tenants:
        status = tenant.payment_status or "UNKNOWN"
        payment_statuses[status] = payment_statuses.get(status, 0) + 1
    
    return {
        "total_active_tenants": len(active_tenants),
        "avg_lease_duration_days": round(avg_lease_duration, 2),
        "payment_statuses": payment_statuses
    }

def get_dashboard_metrics(
    db: Session,
    building_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieves a comprehensive set of metrics for a dashboard.
    """
    # Get various metrics
    occupancy = get_occupancy_rate(db, building_id)
    financial = get_financial_metrics(db, building_id)
    leads = get_lead_conversion_metrics(db)
    maintenance = get_maintenance_metrics(db, building_id)
    rooms = get_room_performance_metrics(db, building_id, 5)  # Top/bottom 5
    tenants = get_tenant_metrics(db, building_id)
    
    # Combine into a single dashboard response
    return {
        "occupancy_metrics": occupancy,
        "financial_metrics": financial,
        "lead_metrics": leads,
        "maintenance_metrics": maintenance,
        "room_metrics": rooms,
        "tenant_metrics": tenants,
        "timestamp": datetime.now().isoformat()
    }

def get_property_comparison(
    db: Session,
    building_ids: List[str]
) -> Dict[str, Any]:
    """
    Compares metrics across multiple properties.
    """
    comparison = {}
    
    for building_id in building_ids:
        # Get building details
        building = db.query(models.Building).filter(models.Building.building_id == building_id).first()
        if not building:
            continue
        
        # Get metrics for this building
        metrics = {
            "occupancy": get_occupancy_rate(db, building_id),
            "financial": get_financial_metrics(db, building_id),
            "maintenance": get_maintenance_metrics(db, building_id),
            "tenants": get_tenant_metrics(db, building_id),
            "building_name": building.building_name,
            "building_address": building.full_address
        }
        
        comparison[building_id] = metrics
    
    return {
        "buildings": comparison,
        "timestamp": datetime.now().isoformat()
    }

def get_lead_source_analysis(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Analyzes lead sources to determine which are most effective.
    """
    # Default to the past 90 days if dates aren't provided
    if not start_date:
        start_date = datetime.now() - timedelta(days=90)
    if not end_date:
        end_date = datetime.now()
    
    # Get all leads with lead_source in the date range
    leads = db.query(models.Lead).filter(
        models.Lead.created_at >= start_date,
        models.Lead.created_at <= end_date,
        models.Lead.lead_source.isnot(None)
    ).all()
    
    # Count leads by source
    sources = {}
    for lead in leads:
        source = lead.lead_source or "UNKNOWN"
        if source not in sources:
            sources[source] = {
                "total": 0,
                "converted": 0,
                "conversion_rate": 0
            }
        
        sources[source]["total"] += 1
        
        # Count as converted if status is LEASE_SIGNED or MOVED_IN
        if lead.status in ["LEASE_SIGNED", "MOVED_IN"]:
            sources[source]["converted"] += 1
    
    # Calculate conversion rates
    for source in sources:
        if sources[source]["total"] > 0:
            sources[source]["conversion_rate"] = round((sources[source]["converted"] / sources[source]["total"]) * 100, 2)
    
    # Sort sources by total leads (descending)
    sorted_sources = sorted(sources.items(), key=lambda x: x[1]["total"], reverse=True)
    
    return {
        "lead_sources": {k: v for k, v in sorted_sources},
        "total_leads_with_source": sum(s["total"] for s in sources.values()),
        "period_start": start_date.strftime("%Y-%m-%d"),
        "period_end": end_date.strftime("%Y-%m-%d")
    }

def get_occupancy_history(
    db: Session,
    building_id: Optional[str] = None,
    months: int = 12
) -> Dict[str, Any]:
    """
    Retrieves historical occupancy data for trend analysis.
    This is a placeholder implementation since we don't have historical data in our current schema.
    """
    # This would typically pull from a separate table tracking historical metrics
    # For now, we'll return a placeholder with the current occupancy
    
    current_occupancy = get_occupancy_rate(db, building_id)
    
    # Create a placeholder history (random data for demonstration)
    history = []
    current_month = datetime.now().replace(day=1)
    
    for i in range(months):
        month = (current_month - timedelta(days=30 * i)).strftime("%Y-%m")
        
        # In a real implementation, this would pull actual historical data
        history.append({
            "month": month,
            "occupancy_rate": current_occupancy["occupancy_rate"] - (i * 2) + (i % 3) * 5  # Fake trend
        })
    
    # Reverse to get chronological order
    history.reverse()
    
    return {
        "occupancy_history": history,
        "current_occupancy": current_occupancy
    }