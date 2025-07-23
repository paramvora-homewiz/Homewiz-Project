# app/ai_services/v3_intelligent_insights_supabase.py
# Analytics and Insights Function - Supabase Version
# Preserves original logic from ai_functions.py with Supabase adaptation

import json
from typing import Dict, Any, Optional
from datetime import datetime
from google import genai
from app.config import GEMINI_API_KEY
from google.genai.types import GenerateContentConfig

# Import the Supabase version of analytics service
from app.services import analytics_service_supabase as analytics_service

client = genai.Client(api_key=GEMINI_API_KEY)

def generate_insights_function(
    insight_type: str,
    building_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Generates analytics and insights for property management.
    This is the Supabase-compatible version that doesn't require db parameter.
    Preserves all original logic from ai_functions.py
    """
    print(f"AI Function Called: generate_insights_function with insight_type: '{insight_type}'")
    
    try:
        # Parse optional parameters (same as original)
        building_id = building_id or kwargs.get("building_id")
        
        # Parse dates if provided (same as original)
        start_date_parsed = None
        end_date_parsed = None
        
        if start_date or ("start_date" in kwargs and kwargs["start_date"]):
            try:
                date_str = start_date or kwargs["start_date"]
                start_date_parsed = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                print(f"Invalid start_date format: {date_str}")
        
        if end_date or ("end_date" in kwargs and kwargs["end_date"]):
            try:
                date_str = end_date or kwargs["end_date"]
                end_date_parsed = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                print(f"Invalid end_date format: {date_str}")
        
        # Generate the insights based on type (same routing logic as original)
        insight_data = {}
        insight_summary = ""
        
        # IMPORTANT: Since analytics_service expects a db parameter but we're using Supabase,
        # we need to either:
        # 1. Modify analytics_service to work without db (recommended)
        # 2. Pass None and let analytics_service handle it
        # 3. Create a mock db object
        
        # For now, we'll assume analytics_service has been updated to work without db
        # or can accept None as db parameter
        
        if insight_type.upper() == "OCCUPANCY":
            # Call without db parameter - Supabase version
            insight_data = analytics_service.get_occupancy_rate(building_id)
            insight_summary = f"Current occupancy rate is {insight_data['occupancy_rate']}% with {insight_data['occupied_rooms']} out of {insight_data['total_rooms']} rooms occupied."
        
        elif insight_type.upper() == "FINANCIAL":
            insight_data = analytics_service.get_financial_metrics(building_id, start_date_parsed, end_date_parsed)
            insight_summary = f"Estimated monthly revenue is ${insight_data['estimated_monthly_revenue']} with average private room rent at ${insight_data['avg_private_rent']}."
        
        elif insight_type.upper() == "LEAD_CONVERSION":
            insight_data = analytics_service.get_lead_conversion_metrics(start_date_parsed, end_date_parsed)
            insight_summary = f"Overall lead conversion rate is {insight_data['overall_conversion_rate']}% with {insight_data['total_leads']} total leads in the period."
        
        elif insight_type.upper() == "MAINTENANCE":
            insight_data = analytics_service.get_maintenance_metrics(building_id, start_date_parsed, end_date_parsed)
            avg_resolution = insight_data.get('avg_resolution_time_hours')
            avg_resolution_text = f"Average resolution time is {avg_resolution} hours." if avg_resolution else "Average resolution time not available."
            insight_summary = f"There were {insight_data['total_requests']} maintenance requests in the period. {avg_resolution_text}"
        
        elif insight_type.upper() == "ROOM_PERFORMANCE":
            insight_data = analytics_service.get_room_performance_metrics(building_id)
            insight_summary = f"Analysis of {insight_data['total_rooms']} rooms showing top and bottom performers based on revenue generation."
        
        elif insight_type.upper() == "TENANT":
            insight_data = analytics_service.get_tenant_metrics(building_id)
            insight_summary = f"There are {insight_data['total_active_tenants']} active tenants with average lease duration of {insight_data['avg_lease_duration_days']} days."
        
        elif insight_type.upper() == "DASHBOARD":
            insight_data = analytics_service.get_dashboard_metrics(building_id)
            insight_summary = "Comprehensive dashboard with occupancy, financial, lead, maintenance, room, and tenant metrics."
        
        else:
            return {
                "success": False,
                "error": f"Invalid insight type: {insight_type}",
                "response": f"'{insight_type}' is not a valid insight type. Please choose from OCCUPANCY, FINANCIAL, LEAD_CONVERSION, MAINTENANCE, ROOM_PERFORMANCE, TENANT, or DASHBOARD."
            }
        
        # Get a detailed analysis from Gemini (same as original)
        detailed_analysis = ""
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=f"""Analyze these {insight_type.lower()} metrics and provide business insights:
                {json.dumps(insight_data, indent=2)}
                
                Focus on key trends, notable metrics, and actionable recommendations.
                Format the analysis in a business-friendly way with clear sections.""",
                config=GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=400
                )
            )
            detailed_analysis = response.text
        except Exception as e:
            detailed_analysis = f"Analysis of {insight_type.lower()} metrics shows {insight_summary}"
            print(f"Gemini analysis error: {e}")
        
        # Return the same structure as original
        return {
            "success": True,
            "insight_type": insight_type,
            "data": insight_data,
            "summary": insight_summary,
            "analysis": detailed_analysis,
            "response": detailed_analysis
        }
    
    except Exception as e:
        error_message = f"Error generating insights: {str(e)}"
        print(error_message)
        return {
            "success": False,
            "error": error_message,
            "response": f"There was a problem generating {insight_type.lower()} insights. Please try again."
        }