# app/services/analytics_service_supabase.py
# Supabase version of analytics service - no db parameter needed

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from app.db.supabase_connection import get_supabase

def get_occupancy_rate(building_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Calculates the current occupancy rate using Supabase.
    """
    supabase = get_supabase()
    
    # Base query for all rooms
    rooms_query = supabase.table('rooms').select('*')
    
    # Filter by building if provided
    if building_id:
        rooms_query = rooms_query.eq('building_id', building_id)
    
    # Get all rooms
    all_rooms_response = rooms_query.execute()
    all_rooms = all_rooms_response.data
    
    # Filter for rooms that are ready to rent (ready_to_rent == True)
    ready_to_rent_rooms = [room for room in all_rooms if room.get('ready_to_rent', False)]
    
    # Count room statuses
    total_rooms = len(all_rooms)
    total_rentable_rooms = len(ready_to_rent_rooms)
    
    # Standardize status comparison - check both cases
    available_rooms = len([room for room in ready_to_rent_rooms 
                          if room.get('status', '').lower() == 'available'])
    occupied_rooms = len([room for room in ready_to_rent_rooms 
                         if room.get('status', '').lower() != 'available'])
    
    # Calculate occupancy percentage based on rentable rooms
    occupancy_rate = 0
    if total_rentable_rooms > 0:
        occupancy_rate = (occupied_rooms / total_rentable_rooms) * 100
    
    return {
        "total_rooms": total_rooms,
        "total_rentable_rooms": total_rentable_rooms,
        "available_rooms": available_rooms,
        "occupied_rooms": occupied_rooms,
        "occupancy_rate": round(occupancy_rate, 2)
    }

def get_financial_metrics(
    building_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Calculates financial metrics using Supabase.
    """
    supabase = get_supabase()
    
    # Default to the current month if dates aren't provided
    if not start_date:
        start_date = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if not end_date:
        next_month = start_date.replace(day=28) + timedelta(days=4)
        end_date = next_month.replace(day=1) - timedelta(days=1)
    

    rooms_query = supabase.table('rooms').select('*').eq('ready_to_rent', True)
    if building_id:
        rooms_query = rooms_query.eq('building_id', building_id)

    response = rooms_query.execute()
    all_rooms = response.data

    # Filter occupied rooms by status != 'AVAILABLE' (case-insensitive)
    occupied_rooms = [room for room in all_rooms if str(room.get('status', '')).upper() != 'AVAILABLE']


    # Calculate total private room rent and shared room rent
    # Ensure we're working with numbers, not strings
    total_private_rent = 0
    for room in occupied_rooms:
        rent = room.get('private_room_rent')
        if rent is not None:
            try:
                total_private_rent += float(rent)
            except (ValueError, TypeError):
                continue
    
    total_shared_rent = 0
    for room in occupied_rooms:
        rent = room.get('shared_room_rent_2')
        if rent is not None:
            try:
                total_shared_rent += float(rent)
            except (ValueError, TypeError):
                continue
    
    # Calculate average rents
    private_rents = []
    for room in occupied_rooms:
        rent = room.get('private_room_rent')
        if rent is not None:
            try:
                private_rents.append(float(rent))
            except (ValueError, TypeError):
                continue
    
    avg_private_rent = sum(private_rents) / len(private_rents) if private_rents else 0
    
    shared_rents = []
    for room in occupied_rooms:
        rent = room.get('shared_room_rent_2')
        if rent is not None:
            try:
                shared_rents.append(float(rent))
            except (ValueError, TypeError):
                continue
    
    avg_shared_rent = sum(shared_rents) / len(shared_rents) if shared_rents else 0
    
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
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Calculates lead conversion metrics using Supabase.
    Returns empty metrics if table doesn't exist.
    """
    try:
        supabase = get_supabase()
        
        # Default to the past 30 days if dates aren't provided
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        # Query leads - try without date filter first to see if we get data
        print(f"Querying leads from {start_date} to {end_date}")
        
        # First, let's try to get all leads to see if the table works
        try:
            test_response = supabase.table('leads').select('*').limit(5).execute()
            print(f"Test query successful, found {len(test_response.data)} leads")
        except Exception as test_error:
            print(f"Test query failed: {test_error}")
            raise test_error
        
        # Now query with date range - format dates properly for Supabase
        leads_query = supabase.table('leads').select('*')
        
        # Supabase expects ISO format with timezone
        start_date_str = start_date.strftime('%Y-%m-%dT%H:%M:%S')
        end_date_str = end_date.strftime('%Y-%m-%dT%H:%M:%S')
        
        leads_query = leads_query.gte('created_at', start_date_str)
        leads_query = leads_query.lte('created_at', end_date_str)
        
        response = leads_query.execute()
        all_leads = response.data
        total_leads = len(all_leads)
        
        print(f"Found {total_leads} leads in date range")
        
        # Count leads by status
        statuses = ["EXPLORING", "SHOWING_SCHEDULED", "APPLICATION_STARTED", 
                    "APPLICATION_SUBMITTED", "LEASE_REQUESTED", "LEASE_SIGNED", 
                    "MOVED_IN", "DECLINED"]
        
        leads_by_status = {}
        for status in statuses:
            count = len([lead for lead in all_leads if str(lead.get('status', '')).upper() == status])
            leads_by_status[status] = count
        
        # Calculate conversion rates
        conversion_rates = {}
        if total_leads > 0:
            for status in statuses:
                conversion_rates[status] = round((leads_by_status[status] / total_leads) * 100, 2)
        else:
            # If no leads in date range, set all rates to 0
            for status in statuses:
                conversion_rates[status] = 0.0
        
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
    
    except Exception as e:
        # Return empty metrics if table doesn't exist or other error
        print(f"Warning: Could not fetch lead metrics: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "total_leads": 0,
            "leads_by_status": {status: 0 for status in ["EXPLORING", "SHOWING_SCHEDULED", "APPLICATION_STARTED", 
                                                         "APPLICATION_SUBMITTED", "LEASE_REQUESTED", "LEASE_SIGNED", 
                                                         "MOVED_IN", "DECLINED"]},
            "conversion_rates": {status: 0.0 for status in ["EXPLORING", "SHOWING_SCHEDULED", "APPLICATION_STARTED", 
                                                           "APPLICATION_SUBMITTED", "LEASE_REQUESTED", "LEASE_SIGNED", 
                                                           "MOVED_IN", "DECLINED"]},
            "overall_conversion_rate": 0.0,
            "period_start": start_date.strftime("%Y-%m-%d") if start_date else "N/A",
            "period_end": end_date.strftime("%Y-%m-%d") if end_date else "N/A",
            "error": f"Lead data error: {str(e)}"
        }

def get_maintenance_metrics(
    building_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Calculates maintenance request metrics using Supabase.
    Returns empty metrics if table doesn't exist.
    """
    try:
        supabase = get_supabase()
        
        # Default to the past 30 days if dates aren't provided
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        # Base query for maintenance requests
        requests_query = supabase.table('maintenance_requests').select('*')
        requests_query = requests_query.gte('created_at', start_date.isoformat())
        requests_query = requests_query.lte('created_at', end_date.isoformat())
        
        # Filter by building if provided
        if building_id:
            requests_query = requests_query.eq('building_id', building_id)
        
        # Get all requests
        response = requests_query.execute()
        all_requests = response.data
        total_requests = len(all_requests)
        
        # Count requests by status
        statuses = ["PENDING", "ASSIGNED", "IN_PROGRESS", "COMPLETED", "CANCELLED"]
        requests_by_status = {}
        for status in statuses:
            count = len([req for req in all_requests if str(req.get('status', '')).upper() == status])
            requests_by_status[status] = count
        
        # Count requests by priority
        priorities = ["LOW", "MEDIUM", "HIGH", "EMERGENCY"]
        requests_by_priority = {}
        for priority in priorities:
            count = len([req for req in all_requests if str(req.get('priority', '')).upper() == priority])
            requests_by_priority[priority] = count
        
        # Calculate average resolution time for completed requests
        avg_resolution_time = None
        completed_requests = [req for req in all_requests 
                             if str(req.get('status', '')).upper() == 'COMPLETED' and req.get('resolved_at')]
        
        if completed_requests:
            resolution_times = []
            for request in completed_requests:
                try:
                    created = datetime.fromisoformat(request['created_at'].replace('Z', '+00:00'))
                    resolved = datetime.fromisoformat(request['resolved_at'].replace('Z', '+00:00'))
                    delta = resolved - created
                    resolution_times.append(delta.total_seconds() / 3600)  # Convert to hours
                except:
                    continue
            
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
    
    except Exception as e:
        # Return empty metrics if table doesn't exist or other error
        print(f"Warning: Could not fetch maintenance metrics: {e}")
        return {
            "total_requests": 0,
            "requests_by_status": {"PENDING": 0, "ASSIGNED": 0, "IN_PROGRESS": 0, "COMPLETED": 0, "CANCELLED": 0},
            "requests_by_priority": {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "EMERGENCY": 0},
            "avg_resolution_time_hours": None,
            "period_start": start_date.strftime("%Y-%m-%d") if start_date else "N/A",
            "period_end": end_date.strftime("%Y-%m-%d") if end_date else "N/A",
            "error": "Maintenance data not available"
        }

def get_room_performance_metrics(
    building_id: Optional[str] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Analyzes room performance using Supabase.
    """
    supabase = get_supabase()
    
    # Base query for all rooms
    rooms_query = supabase.table('rooms').select('*')
    
    # Filter by building if provided
    if building_id:
        rooms_query = rooms_query.eq('building_id', building_id)
    
    # Get all active rooms
    rooms_query = rooms_query.eq('ready_to_rent', True)
    response = rooms_query.execute()
    active_rooms = response.data
    
    # Calculate metrics for each room
    room_metrics = []
    for room in active_rooms:
        # Calculate occupancy duration
        occupancy_duration = 0
        if room.get('booked_from') and room.get('booked_till'):
            try:
                booked_from = datetime.fromisoformat(room['booked_from'])
                booked_till = datetime.fromisoformat(room['booked_till'])
                delta = booked_till - booked_from
                occupancy_duration = delta.days
            except:
                occupancy_duration = 0
        
        # Calculate revenue
        revenue = 0
        if room.get('private_room_rent'):
            try:
                rent = float(room['private_room_rent'])
                revenue = rent * (occupancy_duration / 30)  # Approximate monthly revenue
            except (ValueError, TypeError):
                revenue = 0
        
        room_metrics.append({
            "room_id": room.get('room_id'),
            "room_number": room.get('room_number'),
            "building_id": room.get('building_id'),
            "status": room.get('status'),
            "private_room_rent": room.get('private_room_rent'),
            "shared_room_rent_2": room.get('shared_room_rent_2'),
            "occupancy_duration_days": occupancy_duration,
            "estimated_revenue": round(revenue, 2)
        })
    
    # Sort by estimated revenue (descending)
    sorted_metrics = sorted(room_metrics, key=lambda x: x["estimated_revenue"], reverse=True)
    
    # Get top and bottom performing rooms
    top_performing = sorted_metrics[:limit]
    bottom_performing = sorted_metrics[-limit:] if len(sorted_metrics) >= limit else sorted_metrics
    
    return {
        "total_rooms": len(active_rooms),
        "top_performing_rooms": top_performing,
        "bottom_performing_rooms": bottom_performing
    }

def get_tenant_metrics(building_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyzes tenant data using Supabase.
    """
    supabase = get_supabase()
    
    # Base query for all active tenants
    # tenants_query = supabase.table('tenants').select('*').eq('status', 'ACTIVE')
    tenants_query = supabase.table('tenants').select('*').ilike('status', 'ACTIVE')
    # Filter by building if provided
    if building_id:
        tenants_query = tenants_query.eq('building_id', building_id)
    
    # Get all active tenants
    response = tenants_query.execute()
    active_tenants = response.data
    
    # Calculate lease duration for each tenant
    lease_durations = []
    for tenant in active_tenants:
        if tenant.get('lease_start_date') and tenant.get('lease_end_date'):
            try:
                start_date = datetime.fromisoformat(tenant['lease_start_date'])
                end_date = datetime.fromisoformat(tenant['lease_end_date'])
                delta = end_date - start_date
                lease_durations.append(delta.days)
            except:
                continue
    
    # Calculate average lease duration
    avg_lease_duration = 0
    if lease_durations:
        avg_lease_duration = sum(lease_durations) / len(lease_durations)
    
    # Count payment statuses
    payment_statuses = {}
    for tenant in active_tenants:
        status = str(tenant.get('payment_status', 'UNKNOWN')).upper()
        payment_statuses[status] = payment_statuses.get(status, 0) + 1
    
    return {
        "total_active_tenants": len(active_tenants),
        "avg_lease_duration_days": round(avg_lease_duration, 2),
        "payment_statuses": payment_statuses
    }

def get_dashboard_metrics(building_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieves a comprehensive set of metrics for a dashboard.
    Gracefully handles missing tables.
    """
    dashboard_data = {
        "timestamp": datetime.now().isoformat()
    }
    
    # Get various metrics with error handling
    try:
        dashboard_data["occupancy_metrics"] = get_occupancy_rate(building_id)
    except Exception as e:
        print(f"Warning: Could not fetch occupancy metrics: {e}")
        dashboard_data["occupancy_metrics"] = {"error": "Occupancy data not available"}
    
    try:
        dashboard_data["financial_metrics"] = get_financial_metrics(building_id)
    except Exception as e:
        print(f"Warning: Could not fetch financial metrics: {e}")
        dashboard_data["financial_metrics"] = {"error": "Financial data not available"}
    
    try:
        dashboard_data["lead_metrics"] = get_lead_conversion_metrics()
    except Exception as e:
        print(f"Warning: Could not fetch lead metrics: {e}")
        dashboard_data["lead_metrics"] = {"error": "Lead data not available"}
    
    try:
        dashboard_data["maintenance_metrics"] = get_maintenance_metrics(building_id)
    except Exception as e:
        print(f"Warning: Could not fetch maintenance metrics: {e}")
        dashboard_data["maintenance_metrics"] = {"error": "Maintenance data not available"}
    
    try:
        dashboard_data["room_metrics"] = get_room_performance_metrics(building_id, 5)
    except Exception as e:
        print(f"Warning: Could not fetch room metrics: {e}")
        dashboard_data["room_metrics"] = {"error": "Room performance data not available"}
    
    try:
        dashboard_data["tenant_metrics"] = get_tenant_metrics(building_id)
    except Exception as e:
        print(f"Warning: Could not fetch tenant metrics: {e}")
        dashboard_data["tenant_metrics"] = {"error": "Tenant data not available"}
    
    return dashboard_data