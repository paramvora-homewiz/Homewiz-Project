# app/ai_services/v3_intelligent_insights_supabase.py

import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import re
from google import genai
from app.config import GEMINI_API_KEY
from google.genai.types import GenerateContentConfig
from app.ai_services.gemini_sql_generator import GeminiSQLGenerator
from app.ai_services.sql_executor import SQLExecutor

client = genai.Client(api_key=GEMINI_API_KEY)


def parse_date_from_query(query: str) -> Dict[str, str]:
    """Parse natural language date expressions from query."""
    query_lower = query.lower()
    today = datetime.now()
    
    # Initialize dates
    start_date = None
    end_date = None
    
    # Last quarter
    if "last quarter" in query_lower:
        current_quarter = (today.month - 1) // 3
        if current_quarter == 0:
            # Last quarter of previous year
            start_date = datetime(today.year - 1, 10, 1)
            end_date = datetime(today.year - 1, 12, 31)
        else:
            start_date = datetime(today.year, (current_quarter - 1) * 3 + 1, 1)
            if current_quarter == 1:
                end_date = datetime(today.year, 3, 31)
            elif current_quarter == 2:
                end_date = datetime(today.year, 6, 30)
            else:
                end_date = datetime(today.year, 9, 30)
    
    # This/Current quarter
    elif "this quarter" in query_lower or "current quarter" in query_lower:
        current_quarter = (today.month - 1) // 3
        start_date = datetime(today.year, current_quarter * 3 + 1, 1)
        if current_quarter == 0:
            end_date = datetime(today.year, 3, 31)
        elif current_quarter == 1:
            end_date = datetime(today.year, 6, 30)
        elif current_quarter == 2:
            end_date = datetime(today.year, 9, 30)
        else:
            end_date = datetime(today.year, 12, 31)
    
    # Last month
    elif "last month" in query_lower:
        start_date = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
        end_date = today.replace(day=1) - timedelta(days=1)
    
    # This/Current month
    elif "this month" in query_lower or "current month" in query_lower:
        start_date = today.replace(day=1)
        end_date = (start_date + relativedelta(months=1)) - timedelta(days=1)
    
    # Last year
    elif "last year" in query_lower:
        start_date = datetime(today.year - 1, 1, 1)
        end_date = datetime(today.year - 1, 12, 31)
    
    # This/Current year
    elif "this year" in query_lower or "current year" in query_lower:
        start_date = datetime(today.year, 1, 1)
        end_date = datetime(today.year, 12, 31)
    
    # Last N days
    match = re.search(r'last (\d+) days?', query_lower)
    if match:
        days = int(match.group(1))
        start_date = today - timedelta(days=days)
        end_date = today
    
    # Last N weeks
    match = re.search(r'last (\d+) weeks?', query_lower)
    if match:
        weeks = int(match.group(1))
        start_date = today - timedelta(weeks=weeks)
        end_date = today
    
    # Last N months
    match = re.search(r'last (\d+) months?', query_lower)
    if match:
        months = int(match.group(1))
        start_date = today - relativedelta(months=months)
        end_date = today
    
    # Specific month names
    month_names = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4,
        'may': 5, 'june': 6, 'july': 7, 'august': 8,
        'september': 9, 'october': 10, 'november': 11, 'december': 12
    }
    
    for month_name, month_num in month_names.items():
        if month_name in query_lower:
            # Check if year is specified
            year_match = re.search(rf'{month_name}\s+(\d{{4}})', query_lower)
            if year_match:
                year = int(year_match.group(1))
            else:
                # Assume current year
                year = today.year
            
            start_date = datetime(year, month_num, 1)
            end_date = (start_date + relativedelta(months=1)) - timedelta(days=1)
            break
    
    # Format dates
    result = {}
    if start_date:
        result['start_date'] = start_date.strftime('%Y-%m-%d')
    if end_date:
        result['end_date'] = end_date.strftime('%Y-%m-%d')
    
    return result


def generate_insights_function(
    query: str = None,
    insight_type: str = None,
    building_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Generates analytics and insights using dynamic SQL generation.
    Now handles natural language date parsing from query.
    """
    
    # Extract insight_type from query if not provided
    if not insight_type and query:
        query_lower = query.lower()
        if any(word in query_lower for word in ['best building', 'worst building', 'building performance', 'performing building', 'top building']):
            insight_type = "BUILDING_PERFORMANCE"
        elif any(word in query_lower for word in ['occupancy', 'occupied', 'available']):
            insight_type = "OCCUPANCY"
        elif any(word in query_lower for word in ['revenue', 'financial', 'money', 'income']):
            insight_type = "FINANCIAL"
        elif any(word in query_lower for word in ['lead', 'conversion', 'funnel']):
            insight_type = "LEAD_CONVERSION"
        elif any(word in query_lower for word in ['maintenance', 'repair']):
            insight_type = "MAINTENANCE"
        elif any(word in query_lower for word in ['tenant', 'resident', 'lease']):
            insight_type = "TENANT"
        elif any(word in query_lower for word in ['room performance', 'best room', 'worst room']):
            insight_type = "ROOM_PERFORMANCE"
        elif any(word in query_lower for word in ['dashboard', 'overview', 'summary']):
            insight_type = "DASHBOARD"
        else:
            insight_type = "DASHBOARD"  # Default
    
    print(f"📊 Generating insights for: {insight_type}")
    
    # Parse dates from query if not provided
    if query and not start_date and not end_date:
        parsed_dates = parse_date_from_query(query)
        start_date = start_date or parsed_dates.get('start_date')
        end_date = end_date or parsed_dates.get('end_date')
        
        if start_date or end_date:
            print(f"📅 Parsed dates - Start: {start_date}, End: {end_date}")
    
    try:
        # Prepare context for SQL generation
        context = {
            "building_id": building_id or kwargs.get("building_id"),
            "start_date": start_date or kwargs.get("start_date"),
            "end_date": end_date or kwargs.get("end_date")
        }
        
        # Generate SQL based on insight type
        sql_generator = GeminiSQLGenerator()
        sql_executor = SQLExecutor()
        
        # Define SQL requirements for each insight type
        sql_requirements = _get_sql_requirements_for_insight(insight_type, context)
        
        # Generate SQL
        sql_result = sql_generator.generate_sql(**sql_requirements)
        
        if not sql_result.get('success') or not sql_result.get('sql'):
            return {
                "success": False,
                "error": f"Failed to generate SQL: {sql_result.get('error')}",
                "response": f"Unable to generate {insight_type} insights at this time."
            }
        
        print(f"Generated SQL: {sql_result['sql']}")
        
        # Execute SQL
        query_result = sql_executor.execute_query(sql_result['sql'])
        
        if not query_result['success']:
            return {
                "success": False,
                "error": query_result['error'],
                "response": f"Error retrieving {insight_type} data."
            }
        
        raw_results = query_result['data']

        formatted_data = _format_insight_data(insight_type, raw_results, context)

                # Generate summary
        insight_summary = _generate_insight_summary(insight_type, formatted_data)

        # Pass BOTH raw results and user query for better analysis
        detailed_analysis = _generate_detailed_analysis(
            insight_type, 
            raw_results,  # Pass raw SQL results instead of formatted
            query  # Pass the original user query
        )

        # Add date context to response if dates were parsed
        if start_date or end_date:
            date_context = f" for period {start_date or 'beginning'} to {end_date or 'today'}"
            insight_summary = insight_summary.rstrip('.') + date_context + '.'
        
        return {
            "success": True,
            "insight_type": insight_type,
            "data": formatted_data,
            "summary": insight_summary,
            "analysis": detailed_analysis,
            "response": detailed_analysis,
            "metadata": {
                "sql_query": sql_result['sql'],
                "row_count": query_result['row_count'],
                "context": context,
                "date_range": {"start": start_date, "end": end_date} if (start_date or end_date) else None
            }
        }
        
    except Exception as e:
        error_message = f"Error generating insights: {str(e)}"
        print(f"❌ {error_message}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": error_message,
            "response": f"There was a problem generating {insight_type.lower() if insight_type else 'insights'}. Please try again."
        }


def _get_sql_requirements_for_insight(insight_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Get SQL generation requirements for each insight type."""
    
    insight_type_upper = insight_type.upper()
    
    if insight_type_upper == "OCCUPANCY":
        filters = {}
        if context.get('building_id'):
            filters['building_id'] = context['building_id']
        
        return {
            "filters": filters,
            "query_type": "analytics",
            "tables": ["rooms", "buildings"],
            "joins": [{"from": "rooms", "to": "buildings", "on": "building_id", "type": "LEFT"}],
            "aggregations": [
                {"function": "COUNT", "column": "r.room_id", "alias": "total_rooms"},
                {"function": "SUM", "column": "CASE WHEN r.status = 'Occupied' THEN 1 ELSE 0 END", "alias": "occupied_rooms"},
                {"function": "SUM", "column": "CASE WHEN r.status = 'Available' THEN 1 ELSE 0 END", "alias": "available_rooms"},
                {"function": "ROUND", "column": "(SUM(CASE WHEN r.status = 'Occupied' THEN 1 ELSE 0 END)::numeric / NULLIF(COUNT(r.room_id), 0)::numeric * 100, 2)", "alias": "occupancy_rate"}
            ],
            "group_by": ["b.building_id", "b.building_name"] if not context.get('building_id') else None
        }
    

    # Add this new case after ROOM_PERFORMANCE (around line 260):
    elif insight_type_upper == "BUILDING_PERFORMANCE":
        filters = {}
        if context.get('building_id'):
            filters['building_id'] = context['building_id']
        
        return {
            "filters": filters,
            "query_type": "analytics",
            "tables": ["rooms", "buildings"],
            "joins": [{"from": "rooms", "to": "buildings", "on": "building_id", "type": "INNER"}],
            "aggregations": [
                {"function": "COUNT", "column": "r.room_id", "alias": "total_rooms"},
                {"function": "COUNT", "column": "CASE WHEN r.status = 'Occupied' THEN 1 END", "alias": "occupied_rooms"},
                {"function": "COUNT", "column": "CASE WHEN r.status = 'Available' THEN 1 END", "alias": "available_rooms"},
                {"function": "COALESCE(AVG", "column": "r.private_room_rent), 0)", "alias": "avg_rent"},
                {"function": "COALESCE(SUM", "column": "CASE WHEN r.status = 'Occupied' THEN r.private_room_rent ELSE 0 END), 0)", "alias": "revenue"},
                {"function": "ROUND", "column": "(COUNT(CASE WHEN r.status = 'Occupied' THEN 1 END)::numeric / NULLIF(COUNT(r.room_id), 0)::numeric * 100, 2)", "alias": "occupancy_rate"}
            ],
            "group_by": ["b.building_id", "b.building_name", "b.area"],
            "order_by": [{"column": "revenue", "direction": "DESC"}],
            "limit": 20
        }
    
    elif insight_type_upper == "FINANCIAL":
        filters = {}
        if context.get('building_id'):
            filters['building_id'] = context['building_id']
        
        aggregations = [
            {"function": "COALESCE(SUM", "column": "r.private_room_rent), 0)", "alias": "total_potential_revenue"},
            {"function": "COALESCE(SUM", "column": "CASE WHEN r.status = 'Occupied' THEN r.private_room_rent ELSE 0 END), 0)", "alias": "actual_revenue"},
            {"function": "COALESCE(AVG", "column": "r.private_room_rent), 0)", "alias": "avg_private_rent"},
            {"function": "COALESCE(MIN", "column": "r.private_room_rent), 0)", "alias": "min_rent"},
            {"function": "COALESCE(MAX", "column": "r.private_room_rent), 0)", "alias": "max_rent"}
        ]
        
        return {
            "filters": filters,
            "query_type": "analytics",
            "tables": ["rooms", "buildings"],
            "joins": [{"from": "rooms", "to": "buildings", "on": "building_id", "type": "LEFT"}],
            "aggregations": aggregations,
            "group_by": ["b.building_id", "b.building_name"] if not context.get('building_id') else None
        }
    
    elif insight_type_upper == "LEAD_CONVERSION":
        filters = {}
        # Handle TEXT date columns
        if context.get('start_date'):
            filters['created_after'] = context['start_date']
        if context.get('end_date'):
            filters['created_before'] = context['end_date']
        
        return {
            "filters": filters,
            "query_type": "analytics",
            "tables": ["leads"],
            "aggregations": [
                {"function": "COUNT", "column": "lead_id", "alias": "total_leads"},
                {"function": "COALESCE(SUM", "column": "CASE WHEN status = 'Converted' THEN 1 ELSE 0 END), 0)", "alias": "approved_leads"},
                {"function": "COALESCE(SUM", "column": "CASE WHEN status = 'New' THEN 1 ELSE 0 END), 0)", "alias": "new_leads"},
                {"function": "COALESCE(SUM", "column": "CASE WHEN status = 'Interested' THEN 1 ELSE 0 END), 0)", "alias": "interested"},
                {"function": "COALESCE(SUM", "column": "CASE WHEN status = 'Viewing Scheduled' THEN 1 ELSE 0 END), 0)", "alias": "viewing_scheduled"},
                {"function": "COALESCE(SUM", "column": "CASE WHEN status = 'Application Submitted' THEN 1 ELSE 0 END), 0)", "alias": "application_submitted"},
                {"function": "COALESCE(SUM", "column": "CASE WHEN status = 'Lost' THEN 1 ELSE 0 END), 0)", "alias": "lost"},
                {"function": "ROUND", "column": "(COALESCE(SUM(CASE WHEN status = 'Converted' THEN 1 ELSE 0 END), 0)::numeric / NULLIF(COUNT(lead_id), 0)::numeric * 100, 2)", "alias": "conversion_rate"}
            ]
        }
    
    elif insight_type_upper == "MAINTENANCE":
        filters = {}
        if context.get('building_id'):
            filters['building_id'] = context['building_id']
        
        # Fixed to handle TEXT date columns
        return {
            "filters": filters,
            "query_type": "analytics",
            "tables": ["rooms", "buildings"],
            "joins": [{"from": "rooms", "to": "buildings", "on": "building_id", "type": "LEFT"}],
            "aggregations": [
                {"function": "COUNT", "column": "CASE WHEN r.status = 'Maintenance' THEN 1 END", "alias": "total_maintenance"},
                {"function": "COUNT", "column": "CASE WHEN r.last_check IS NOT NULL AND r.last_check::date < CURRENT_DATE - INTERVAL '30 days' THEN 1 END", "alias": "overdue_checks"},
                {"function": "COUNT", "column": "CASE WHEN r.last_check IS NOT NULL AND r.last_check::date >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END", "alias": "recent_checks"}
            ],
            "group_by": ["b.building_id", "b.building_name"] if not context.get('building_id') else None
        }
    
    elif insight_type_upper == "ROOM_PERFORMANCE":
        filters = {}
        if context.get('building_id'):
            filters['building_id'] = context['building_id']
        
        return {
            "filters": filters,
            "query_type": "search",
            "tables": ["rooms", "buildings"],
            "joins": [{"from": "rooms", "to": "buildings", "on": "building_id", "type": "LEFT"}],
            "order_by": [{"column": "r.private_room_rent", "direction": "DESC"}],
            "limit": 100
        }
    
    elif insight_type_upper == "TENANT":
        filters = {"tenant_status": "Active"}
        if context.get('building_id'):
            filters['building_id'] = context['building_id']
        
        # Fixed date calculation - direct subtraction returns days
        return {
            "filters": filters,
            "query_type": "analytics",
            "tables": ["tenants", "rooms", "buildings"],
            "joins": [
                {"from": "tenants", "to": "rooms", "on": "room_id", "type": "LEFT"},
                {"from": "rooms", "to": "buildings", "on": "building_id", "type": "LEFT"}
            ],
            "aggregations": [
                {"function": "COUNT", "column": "t.tenant_id", "alias": "total_active_tenants"},
                {"function": "COALESCE(SUM", "column": "CASE WHEN t.payment_status = 'Current' THEN 1 ELSE 0 END), 0)", "alias": "current_payments"},
                {"function": "COALESCE(SUM", "column": "CASE WHEN t.payment_status = 'Late' THEN 1 ELSE 0 END), 0)", "alias": "late_payments"},
                {"function": "COALESCE(AVG", "column": "CASE WHEN t.lease_start_date IS NOT NULL THEN (CURRENT_DATE - t.lease_start_date::date) END), 0)", "alias": "avg_lease_duration_days"}
            ],
            "group_by": ["b.building_id", "b.building_name"] if not context.get('building_id') else None
        }
    
    elif insight_type_upper == "DASHBOARD":
        return {
            "filters": {},
            "query_type": "analytics",
            "tables": ["rooms", "buildings"],
            "joins": [{"from": "rooms", "to": "buildings", "on": "building_id", "type": "LEFT"}],
            "aggregations": [
                {"function": "COUNT", "column": "DISTINCT r.room_id", "alias": "total_rooms"},
                {"function": "COUNT", "column": "DISTINCT b.building_id", "alias": "total_buildings"},
                {"function": "COALESCE(AVG", "column": "r.private_room_rent), 0)", "alias": "avg_rent"},
                {"function": "SUM", "column": "CASE WHEN r.status = 'Occupied' THEN 1 ELSE 0 END", "alias": "occupied_rooms"}
            ]
        }
    
    else:
        return {
            "filters": {},
            "query_type": "analytics",
            "tables": ["rooms"],
            "aggregations": [{"function": "COUNT", "column": "*", "alias": "count"}]
        }


def _format_insight_data(insight_type: str, raw_data: list, context: Dict[str, Any]) -> Dict[str, Any]:
    """Format raw SQL results into expected structure for each insight type."""
    
    insight_type_upper = insight_type.upper()
    
    # Helper to safely convert to float
    def safe_float(value, default=0):
        if value is None:
            return default
        try:
            return float(value)
        except (TypeError, ValueError):
            return default
    
    # Helper to safely convert to int
    def safe_int(value, default=0):
        if value is None:
            return default
        try:
            return int(value)
        except (TypeError, ValueError):
            return default
    
    if insight_type_upper == "OCCUPANCY":
        if len(raw_data) == 1:
            row = raw_data[0]
            return {
                "total_rooms": safe_int(row.get('total_rooms', 0)),
                "occupied_rooms": safe_int(row.get('occupied_rooms', 0)),
                "available_rooms": safe_int(row.get('available_rooms', 0)),
                "occupancy_rate": safe_float(row.get('occupancy_rate', 0)),
                "building_name": row.get('building_name', 'All Buildings')
            }
        else:
            return {
                "by_building": raw_data,
                "total_rooms": sum(safe_int(r.get('total_rooms', 0)) for r in raw_data),
                "occupied_rooms": sum(safe_int(r.get('occupied_rooms', 0)) for r in raw_data),
                "available_rooms": sum(safe_int(r.get('available_rooms', 0)) for r in raw_data),
                "occupancy_rate": _calculate_overall_rate(raw_data, 'occupied_rooms', 'total_rooms')
            }
        

    elif insight_type_upper == "BUILDING_PERFORMANCE":
        if raw_data:
            # Sort by revenue to get best/worst performers
            sorted_by_revenue = sorted(raw_data, key=lambda x: safe_float(x.get('revenue', 0)), reverse=True)
            
            return {
                "total_buildings": len(raw_data),
                "buildings": sorted_by_revenue,
                "top_performer": sorted_by_revenue[0] if sorted_by_revenue else None,
                "bottom_performer": sorted_by_revenue[-1] if len(sorted_by_revenue) > 1 else None,
                "avg_occupancy_rate": _safe_average(raw_data, 'occupancy_rate'),
                "total_revenue": sum(safe_float(r.get('revenue', 0)) for r in raw_data),
                "avg_rent_across_buildings": _safe_average(raw_data, 'avg_rent')
            }
        return {
            "total_buildings": 0,
            "buildings": [],
            "top_performer": None,
            "bottom_performer": None
        }  
    
    elif insight_type_upper == "FINANCIAL":
        if len(raw_data) == 1:
            row = raw_data[0]
            total_potential = safe_float(row.get('total_potential_revenue', 0))
            actual = safe_float(row.get('actual_revenue', 0))
            
            return {
                "total_potential_revenue": total_potential,
                "actual_revenue": actual,
                "avg_private_rent": safe_float(row.get('avg_private_rent', 0)),
                "min_rent": safe_float(row.get('min_rent', 0)),
                "max_rent": safe_float(row.get('max_rent', 0)),
                "revenue_realization_rate": _safe_percentage(actual, total_potential),
                "estimated_monthly_revenue": actual  # For backward compatibility
            }
        else:
            total_potential = sum(safe_float(r.get('total_potential_revenue', 0)) for r in raw_data)
            actual = sum(safe_float(r.get('actual_revenue', 0)) for r in raw_data)
            
            return {
                "by_building": raw_data,
                "total_potential_revenue": total_potential,
                "actual_revenue": actual,
                "avg_private_rent": _safe_average(raw_data, 'avg_private_rent'),
                "revenue_realization_rate": _safe_percentage(actual, total_potential),
                "estimated_monthly_revenue": actual
            }
    
    elif insight_type_upper == "LEAD_CONVERSION":
        if raw_data:
            row = raw_data[0]
            total_leads = safe_int(row.get('total_leads', 0))
            approved = safe_int(row.get('approved_leads', 0))
            
            return {
                "total_leads": total_leads,
                "approved_leads": approved,
                "new_leads": safe_int(row.get('new_leads', 0)),
                "interested": safe_int(row.get('interested', 0)),
                "viewing_scheduled": safe_int(row.get('viewing_scheduled', 0)),
                "application_submitted": safe_int(row.get('application_submitted', 0)),
                "lost": safe_int(row.get('lost', 0)),
                "conversion_rate": safe_float(row.get('conversion_rate', 0)),
                "overall_conversion_rate": safe_float(row.get('conversion_rate', 0)),  # For backward compatibility
                "funnel": {
                    "New": safe_int(row.get('new_leads', 0)),
                    "Interested": safe_int(row.get('interested', 0)),
                    "Viewing Scheduled": safe_int(row.get('viewing_scheduled', 0)),
                    "Application Submitted": safe_int(row.get('application_submitted', 0)),
                    "Converted": approved,
                    "Lost": safe_int(row.get('lost', 0))
                }
            }
        return {
            "total_leads": 0,
            "conversion_rate": 0,
            "overall_conversion_rate": 0,
            "funnel": {}
        }
    
    elif insight_type_upper == "MAINTENANCE":
        if len(raw_data) == 1:
            row = raw_data[0]
            return {
                "total_requests": safe_int(row.get('total_maintenance', 0)),
                "total_maintenance_requests": safe_int(row.get('total_maintenance', 0)),
                "overdue_checks": safe_int(row.get('overdue_checks', 0)),
                "recent_checks": safe_int(row.get('recent_checks', 0)),
                "avg_resolution_time_hours": None,  # Would need separate query
                "maintenance_compliance_rate": _safe_percentage(
                    safe_int(row.get('recent_checks', 0)),
                    safe_int(row.get('total_rooms', 1))
                )
            }
        else:
            total_maintenance = sum(safe_int(r.get('total_maintenance', 0)) for r in raw_data)
            overdue = sum(safe_int(r.get('overdue_checks', 0)) for r in raw_data)
            recent = sum(safe_int(r.get('recent_checks', 0)) for r in raw_data)
            
            return {
                "by_building": raw_data,
                "total_requests": total_maintenance,
                "total_maintenance_requests": total_maintenance,
                "overdue_checks": overdue,
                "recent_checks": recent,
                "avg_resolution_time_hours": None
            }
    
    elif insight_type_upper == "ROOM_PERFORMANCE":
        # Filter out None values in rent
        valid_rooms = [r for r in raw_data if r.get('private_room_rent') is not None]
        sorted_by_rent = sorted(valid_rooms, key=lambda x: safe_float(x.get('private_room_rent', 0)), reverse=True)
        
        return {
            "total_rooms": len(valid_rooms),
            "top_performers": sorted_by_rent[:10],
            "bottom_performers": sorted_by_rent[-10:] if len(sorted_by_rent) > 10 else [],
            "avg_rent": _safe_average(valid_rooms, 'private_room_rent'),
            "occupancy_by_price_range": _group_by_price_range(valid_rooms)
        }
    
    elif insight_type_upper == "TENANT":
        if len(raw_data) == 1:
            row = raw_data[0]
            total_tenants = safe_int(row.get('total_active_tenants', 0))
            current = safe_int(row.get('current_payments', 0))
            
            return {
                "total_active_tenants": total_tenants,
                "current_payments": current,
                "late_payments": safe_int(row.get('late_payments', 0)),
                "avg_lease_duration_days": safe_float(row.get('avg_lease_duration_days', 0)),
                "payment_compliance_rate": _safe_percentage(current, total_tenants)
            }
        else:
            total_tenants = sum(safe_int(r.get('total_active_tenants', 0)) for r in raw_data)
            current = sum(safe_int(r.get('current_payments', 0)) for r in raw_data)
            late = sum(safe_int(r.get('late_payments', 0)) for r in raw_data)
            
            return {
                "by_building": raw_data,
                "total_active_tenants": total_tenants,
                "current_payments": current,
                "late_payments": late,
                "avg_lease_duration_days": _safe_average(raw_data, 'avg_lease_duration_days'),
                "payment_compliance_rate": _safe_percentage(current, total_tenants)
            }
    
    elif insight_type_upper == "DASHBOARD":
        if raw_data:
            row = raw_data[0]
            return {
                "total_rooms": safe_int(row.get('total_rooms', 0)),
                "total_buildings": safe_int(row.get('total_buildings', 0)),
                "occupied_rooms": safe_int(row.get('occupied_rooms', 0)),
                "avg_rent": safe_float(row.get('avg_rent', 0)),
                "occupancy_rate": _safe_percentage(
                    safe_int(row.get('occupied_rooms', 0)),
                    safe_int(row.get('total_rooms', 1))
                )
            }
        return {
            "total_rooms": 0,
            "total_buildings": 0,
            "occupied_rooms": 0,
            "avg_rent": 0,
            "occupancy_rate": 0
        }
    
    else:
        return {"data": raw_data}


def _generate_insight_summary(insight_type: str, data: Dict[str, Any]) -> str:
    """Generate a summary sentence for the insight."""
    
    insight_type_upper = insight_type.upper()
    
    if insight_type_upper == "OCCUPANCY":
        return f"Current occupancy rate is {data.get('occupancy_rate', 0):.1f}% with {data.get('occupied_rooms', 0)} out of {data.get('total_rooms', 0)} rooms occupied."
    
    elif insight_type_upper == "FINANCIAL":
        revenue = data.get('actual_revenue', 0)
        potential = data.get('total_potential_revenue', 0)
        realization = data.get('revenue_realization_rate', 0)
        return f"Total potential monthly revenue is ${potential:,.2f} with actual revenue at ${revenue:,.2f} ({realization:.1f}% realization)."
    
    elif insight_type_upper == "LEAD_CONVERSION":
        return f"Lead conversion rate is {data.get('conversion_rate', 0):.1f}% with {data.get('approved_leads', 0)} converted out of {data.get('total_leads', 0)} total leads."
    
    elif insight_type_upper == "MAINTENANCE":
        return f"There are {data.get('total_maintenance_requests', 0)} maintenance items with {data.get('overdue_checks', 0)} overdue checks."
    
    elif insight_type_upper == "TENANT":
        compliance = data.get('payment_compliance_rate', 0)
        return f"Total of {data.get('total_active_tenants', 0)} active tenants with {compliance:.1f}% payment compliance rate."
    
    elif insight_type_upper == "ROOM_PERFORMANCE":
        return f"Analysis of {data.get('total_rooms', 0)} rooms with average rent of ${data.get('avg_rent', 0):,.2f}."
    
    elif insight_type_upper == "BUILDING_PERFORMANCE":
        if data.get('top_performer'):
            top = data['top_performer']
            return f"Best performing building is {top.get('building_name', 'Unknown')} with ${top.get('revenue', 0):,.2f} revenue and {top.get('occupancy_rate', 0):.1f}% occupancy."
        return "Building performance analysis complete."
    
    else:
        return f"{insight_type} data has been compiled."


def _generate_detailed_analysis(insight_type: str, raw_data: list, user_query: str) -> str:
    """Generate analysis from raw SQL results."""
    
    try:
        # Convert to JSON-safe format
        data_sample = raw_data[:10] if len(raw_data) > 10 else raw_data
        clean_data = json.loads(json.dumps(data_sample, default=str))
        
        prompt = f"""
User asked: "{user_query}"

Here are the query results:
{json.dumps(clean_data, indent=2)}

Total results: {len(raw_data)}

Provide a direct answer to the user's question. Be specific with names, numbers, and percentages.
Focus on what the user asked for, not generic insights.
Keep response under 3-4 sentences.
"""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=200
            )
        )
        
        return response.text.strip()
        
    except Exception as e:
        print(f"Gemini analysis error: {e}")
        # Fallback to basic summary
        return f"Found {len(raw_data)} results for your {insight_type.lower()} query."


# Helper functions
def _calculate_overall_rate(data: list, numerator_field: str, denominator_field: str) -> float:
    """Calculate overall rate from aggregated data."""
    def safe_get(row, field, default=0):
        value = row.get(field, default)
        return float(value) if value is not None else default
    
    total_num = sum(safe_get(r, numerator_field) for r in data)
    total_den = sum(safe_get(r, denominator_field) for r in data)
    return round((total_num / total_den * 100) if total_den > 0 else 0, 2)


def _safe_percentage(numerator: float, denominator: float) -> float:
    """Calculate percentage safely."""
    if numerator is None:
        numerator = 0
    if denominator is None or denominator == 0:
        return 0
    return round((float(numerator) / float(denominator) * 100), 2)


def _safe_average(data: list, field: str) -> float:
    """Calculate average safely."""
    values = []
    for r in data:
        value = r.get(field)
        if value is not None:
            try:
                values.append(float(value))
            except (TypeError, ValueError):
                continue
    
    return round(sum(values) / len(values), 2) if values else 0


def _group_by_price_range(rooms: list) -> Dict[str, int]:
    """Group rooms by price range."""
    ranges = {
        "under_1500": 0,
        "1500_2000": 0,
        "2000_2500": 0,
        "2500_3000": 0,
        "over_3000": 0
    }
    
    for room in rooms:
        rent = room.get('private_room_rent')
        if rent is None:
            continue
        
        try:
            rent_float = float(rent)
            if rent_float < 1500:
                ranges["under_1500"] += 1
            elif rent_float < 2000:
                ranges["1500_2000"] += 1
            elif rent_float < 2500:
                ranges["2000_2500"] += 1
            elif rent_float < 3000:
                ranges["2500_3000"] += 1
            else:
                ranges["over_3000"] += 1
        except (TypeError, ValueError):
            continue
    
    return ranges