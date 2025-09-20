# app/ai_services/result_verifier.py

from typing import Dict, Any, List, Union, Optional
from pydantic import BaseModel, Field
from app.db.database_schema import DATABASE_SCHEMA
from app.ai_services.text_response_formatter import TextResponseFormatter
import json

class FrontendResponse(BaseModel):
    """Guaranteed response structure for frontend."""
    success: bool
    data: List[Dict[str, Any]]
    message: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

class ResultVerifier:
    """
    Verifies and structures results to prevent hallucination in responses.
    """
    
    def __init__(self):
        self.schema = DATABASE_SCHEMA
        self.result_schemas = self._build_result_schemas()
    
    async def verify_and_structure(
        self,
        raw_results: Dict[str, Any],
        original_query: str,
        sql_query: str,
        user_context: Dict[str, Any]
    ) -> FrontendResponse:
        """
        Verify results against schema and structure for frontend.
        """
        
        if not raw_results.get("success"):
            return FrontendResponse(
                success=False,
                data=[],
                message=f"Query execution failed: {raw_results.get('error')}",
                errors=[raw_results.get('error', 'Unknown error')]
            )
        
        # Determine expected result type from query
        result_type = await self._determine_result_type(original_query, sql_query)
        
        # Verify data integrity
        verification_result = await self._verify_data_integrity(
            raw_results["data"], result_type
        )
        
        if not verification_result["valid"]:
            return FrontendResponse(
                success=False,
                data=[],
                message="Data verification failed - possible hallucination detected",
                errors=verification_result["errors"]
            )
        
        # Structure for frontend
        structured_data = await self._structure_for_frontend(
            raw_results["data"], result_type, original_query
        )
        
        # Generate human-readable message
        message = await self._generate_response_message(
            structured_data, original_query, user_context
        )
        
        return FrontendResponse(
            success=True,
            data=structured_data,
            message=message,
            metadata={
                "sql_query": sql_query,
                "row_count": len(raw_results["data"]),
                "result_type": result_type,
                "execution_time": raw_results.get("execution_time", 0)
            }
        )
    
    async def _determine_result_type(self, original_query: str, sql_query: str) -> str:
        """Determine the type of result based on query and SQL."""
        query_lower = original_query.lower()
        sql_lower = sql_query.lower()
        
        # Analytics patterns (check first to avoid conflicts)
        if any(word in query_lower for word in ['occupancy', 'rate', 'revenue', 'analytics', 'report', 'metrics', 'statistics', 'calculate', 'total', 'average', 'sum']):
            return "analytics"
        sql_lower = sql_query.lower()
        if any(func in sql_lower for func in ['count(', 'sum(', 'avg(', 'max(', 'min(']):
            return "analytics"
        # Tenant management patterns
        if any(word in query_lower for word in ['tenant', 'resident', 'lease', 'payment', 'active tenant', 'late payment']):
            return "tenant_management"
        # Tour Scheduling Patterns:
        if any(word in query_lower for word in ['tour', 'slot', 'viewing', 'appointment', 'schedule']):
            return "tour_scheduling"
        # Lead management patterns
        if any(word in query_lower for word in ['lead', 'prospect', 'showing', 'conversion', 'interested']):
            return "lead_management"
        
        # Maintenance patterns
        if any(word in query_lower for word in ['maintenance', 'repair', 'issue', 'request']):
            return "maintenance"
        
        # Property search patterns (default for room-related queries)
        if any(word in query_lower for word in ['room', 'apartment', 'property', 'available', 'find', 'search', 'show', 'cheapest', 'wifi', 'bathroom']):
            return "property_search"
        
        # Default to generic
        return "generic"
    
    async def _verify_data_integrity(
        self, 
        data: List[Dict], 
        expected_type: str
    ) -> Dict[str, Any]:
        """Verify that returned data matches expected schema."""
        
        verification_result = {"valid": True, "errors": []}
        
        if not data:
            return verification_result  # Empty results are valid
        
        # Get all valid column names from schema
        valid_columns = set()
        for table_name, table_info in self.schema["tables"].items():
            valid_columns.update(table_info["columns"].keys())
        
        # Common SQL aliases and calculated columns that are acceptable
        acceptable_aliases = {
            'total_rooms', 'available_rooms', 'occupied_rooms', 'vacant_rooms',
            'occupancy_rate', 'revenue', 'total_revenue', 'avg_rent',
            'total_count', 'count', 'sum', 'avg', 'min', 'max',
            'metric_name', 'metric_value', 'time_period', 'previous_value',
            'change_percentage', 'percentage', 'average_value',
            # Additional common aliases
            'total_operators', 'total_buildings', 'total_tenants', 'total_leads',
            'active_tenants', 'inactive_tenants', 'pending_tenants',
            'new_leads', 'interested_leads', 'converted_leads',
            'maintenance_rooms', 'reserved_rooms',
            'building_count', 'room_count', 'tenant_count', 'lead_count',
            'operator_count', 'maintenance_count'
        }
        
        for row_idx, row in enumerate(data):
            for column, value in row.items():
                # Check if column is in schema or is an acceptable alias
                if column in valid_columns or column in acceptable_aliases:
                    # Only validate schema columns, not aliases
                    if column in valid_columns:
                        for table_name, table_info in self.schema["tables"].items():
                            if column in table_info["columns"]:
                                col_info = table_info["columns"][column]
                                if not self._validate_column_value(value, col_info):
                                    verification_result["valid"] = False
                                    verification_result["errors"].append(
                                        f"Row {row_idx + 1}: Invalid value '{value}' for column '{column}'"
                                    )
                                break
                else:
                    # Log unknown columns as warnings instead of errors
                    verification_result["errors"].append(f"Row {row_idx + 1}: Unknown column '{column}' in results (may be SQL alias)")
        
        return verification_result
    
    def _validate_column_value(self, value: Any, col_info: Dict[str, Any]) -> bool:
        """Validate a column value against its schema definition."""
        
        # Handle null values
        if value is None:
            return col_info.get("nullable", True)
        
        # Basic type validation
        col_type = col_info["type"].upper()
        
        if "TEXT" in col_type or "VARCHAR" in col_type:
            return isinstance(value, str)
        elif "BIGINT" in col_type or "INTEGER" in col_type:
            return isinstance(value, (int, str)) and str(value).isdigit()
        elif "DOUBLE" in col_type or "NUMERIC" in col_type:
            try:
                float(value)
                return True
            except (ValueError, TypeError):
                return False
        elif "BOOLEAN" in col_type:
            return isinstance(value, bool) or value in ['true', 'false', '1', '0']
        elif "TIMESTAMP" in col_type:
            return isinstance(value, str)  # Timestamps are stored as text in this schema
        elif "JSONB" in col_type:
            try:
                if isinstance(value, str):
                    json.loads(value)
                return True
            except json.JSONDecodeError:
                return False
        
        return True  # Default to valid for unknown types
    
    async def _structure_for_frontend(
        self,
        raw_data: List[Dict],
        result_type: str,
        original_query: str
    ) -> List[Dict[str, Any]]:
        """Structure data according to frontend expectations."""
        
        if result_type == "property_search":
            return [self._structure_property_result(row) for row in raw_data]
        elif result_type == "tour_scheduling":
            return [self._structure_tour_result(row) for row in raw_data]
        elif result_type == "analytics":
            return [self._structure_analytics_result(row) for row in raw_data]
        elif result_type == "tenant_management":
            return [self._structure_tenant_result(row) for row in raw_data]
        elif result_type == "lead_management":
            return [self._structure_lead_result(row) for row in raw_data]
        elif result_type == "maintenance":
            return [self._structure_maintenance_result(row) for row in raw_data]
        else:
            return [self._structure_generic_result(row) for row in raw_data]
    
    def _structure_property_result(self, row: Dict) -> Dict[str, Any]:
        """Structure property search results."""
        return {
            "id": row.get("room_id"),
            "title": f"Room {row.get('room_number', 'N/A')} - {row.get('building_name', 'Unknown Building')}",
            "rent": float(row.get("private_room_rent", 0)) if row.get("private_room_rent") else 0,
            "status": row.get("status", "Unknown"),
            "building": {
                "id": row.get("building_id"),
                "name": row.get("building_name"),
                "address": row.get("full_address") or row.get("street", "")
            },
            "details": {
                "room_number": str(row.get("room_number", "")),
                "square_footage": row.get("sq_footage"),
                "view": row.get("view"),
                "bathroom_type": row.get("bathroom_type"),
                "bed_type": row.get("bed_type"),
                "floor_number": row.get("floor_number")
            },
            "amenities": {
                "wifi": row.get("wifi_included", False),
                "laundry": row.get("laundry_onsite", False),
                "fitness": row.get("fitness_area", False),
                "pet_friendly": row.get("pet_friendly", "No")
            }
        }
    def _structure_tour_result(self, row: Dict) -> Dict[str, Any]:
        """Structure tour scheduling results."""
        return {
            "slot_id": row.get("slot_id") or row.get("tour_id"),
            "slot_date": row.get("slot_date") or row.get("scheduled_date"),
            "slot_time": row.get("slot_time") or row.get("scheduled_time"),
            "room_id": row.get("room_id"),
            "room_number": row.get("room_number"),
            "building_name": row.get("building_name"),
            "is_available": row.get("is_available") or (row.get("status") == "Scheduled"),
            "duration": row.get("slot_duration") or row.get("duration_minutes", 30),
            "status": row.get("status"),
            "tour_type": row.get("tour_type")
    }
       
    def _structure_analytics_result(self, row: Dict) -> Dict[str, Any]:
        """Structure analytics results."""
        # Handle different types of analytics data
        if "building_name" in row:
            # Building-based analytics
            return {
                "metric_name": row.get("metric_name", "Building Metric"),
                "metric_value": row.get("metric_value") or row.get("total_revenue") or row.get("occupancy_rate") or row.get("total_rooms", 0),
                "time_period": row.get("time_period"),
                "building_name": row.get("building_name"),
                "comparison": {
                    "previous_period": row.get("previous_value"),
                    "change_percentage": row.get("change_percentage")
                },
                "details": {
                    "total_count": row.get("total_count") or row.get("total_rooms"),
                    "percentage": row.get("percentage") or row.get("occupancy_rate"),
                    "average": row.get("average_value") or row.get("avg_rent"),
                    "available_rooms": row.get("available_rooms"),
                    "occupied_rooms": row.get("occupied_rooms"),
                    "total_revenue": row.get("total_revenue")
                }
            }
        if 'scheduled_tours' in row and 'completed_tours' in row:
            return {
                "scheduled_tours": row.get("scheduled_tours", 0),
                "completed_tours": row.get("completed_tours", 0),
                "type": "tour_summary"
            }
        else:
            # Generic analytics
            return {
                "metric_name": row.get("metric_name", "System Metric"),
                "metric_value": row.get("metric_value", 0),
                "time_period": row.get("time_period"),
                "building_name": None,
                "comparison": {
                    "previous_period": row.get("previous_value"),
                    "change_percentage": row.get("change_percentage")
                },
                "details": {
                    "total_count": row.get("total_count"),
                    "percentage": row.get("percentage"),
                    "average": row.get("average_value")
                }
            }
    
    def _structure_tenant_result(self, row: Dict) -> Dict[str, Any]:
        """Structure tenant management results."""
        return {
            "id": row.get("tenant_id"),
            "name": row.get("tenant_name"),
            "email": row.get("tenant_email"),
            "phone": row.get("phone"),
            "status": row.get("status", "Unknown"),
            "room": {
                "id": row.get("room_id"),
                "number": str(row.get("room_number", "")),
                "building_name": row.get("building_name")
            },
            "lease": {
                "start_date": row.get("lease_start_date"),
                "end_date": row.get("lease_end_date"),
                "booking_type": row.get("booking_type")
            },
            "payment": {
                "status": row.get("payment_status"),
                "last_payment": row.get("last_payment_date"),
                "next_payment": row.get("next_payment_date"),
                "deposit": row.get("deposit_amount")
            }
        }
    
    def _structure_lead_result(self, row: Dict) -> Dict[str, Any]:
        """Structure lead management results."""
        return {
            "id": row.get("lead_id"),
            "email": row.get("email"),
            "status": row.get("status", "Unknown"),
            "interaction_count": row.get("interaction_count", 0),
            "selected_room": {
                "id": row.get("selected_room_id"),
                "number": str(row.get("room_number", ""))
            },
            "timeline": {
                "planned_move_in": row.get("planned_move_in"),
                "planned_move_out": row.get("planned_move_out"),
                "last_contacted": row.get("last_contacted"),
                "next_follow_up": row.get("next_follow_up")
            },
            "preferences": {
                "budget_min": row.get("budget_min"),
                "budget_max": row.get("budget_max"),
                "preferred_lease_term": row.get("preferred_lease_term")
            }
        }
    
    def _structure_maintenance_result(self, row: Dict) -> Dict[str, Any]:
        """Structure maintenance request results."""
        return {
            "id": row.get("request_id"),
            "title": row.get("title"),
            "description": row.get("description"),
            "status": row.get("status", "Unknown"),
            "priority": row.get("priority", "Medium"),
            "room": {
                "id": row.get("room_id"),
                "number": str(row.get("room_number", "")),
                "building_name": row.get("building_name")
            },
            "tenant": {
                "id": row.get("tenant_id"),
                "name": row.get("tenant_name")
            },
            "timeline": {
                "created_at": row.get("created_at"),
                "updated_at": row.get("updated_at"),
                "estimated_completion": row.get("estimated_completion")
            }
        }
    
    def _structure_generic_result(self, row: Dict) -> Dict[str, Any]:
        """Structure generic results."""
        return {
            "data": row,
            "type": "generic"
        }
    
    async def _generate_response_message(
    self,
    structured_data: List[Dict],
    original_query: str,
    user_context: Dict[str, Any]
) -> str:
        """Generate contextual response message using LLM formatter."""
        
        # Use the new text formatter for all responses
        formatter = TextResponseFormatter()
        
        # Determine result type from the structured data
        result_type = "generic"
        if structured_data:
            # Check first item to determine type
            first_item = structured_data[0]
            if "room_id" in first_item and "building_name" in first_item:
                result_type = "property_search"
            elif "metric_name" in first_item or "metric_value" in first_item:
                result_type = "analytics"
            elif "tenant_id" in first_item:
                result_type = "tenant_management"
            elif "lead_id" in first_item:
                result_type = "lead_management"
            elif "slot_id" in first_item or "tour_id" in first_item:
                result_type = "tour_scheduling"
            elif "request_id" in first_item:
                result_type = "maintenance"
        
        try:
            # Generate formatted response
            formatted_message = await formatter.format_response(
                data=structured_data,
                original_query=original_query,
                result_type=result_type
            )
            return formatted_message
        except Exception as e:
            # Fallback to original simple message generation
            return self._generate_simple_response_message(structured_data, original_query, result_type)

    def _generate_simple_response_message(
        self,
        structured_data: List[Dict],
        original_query: str,
        result_type: str
    ) -> str:
        """Fallback simple message generation (original logic)."""
        
        if not structured_data:
            return f"No results found for '{original_query}'. Try adjusting your search criteria."
        
        count = len(structured_data)
        query_lower = original_query.lower()
        
        # Original message generation logic
        if any(word in query_lower for word in ['room', 'apartment', 'property', 'available']):
            return f"Found {count} property{'ies' if count != 1 else ''} matching your criteria."
        elif any(word in query_lower for word in ['occupancy', 'rate']):
            return f"Retrieved occupancy data for {count} building{'s' if count != 1 else ''}."
        elif any(word in query_lower for word in ['tenant', 'resident']):
            return f"Found {count} tenant{'s' if count != 1 else ''} matching your criteria."
        elif any(word in query_lower for word in ['lead', 'prospect']):
            return f"Retrieved {count} lead{'s' if count != 1 else ''} from the system."
        elif any(word in query_lower for word in ['maintenance', 'repair']):
            return f"Found {count} maintenance request{'s' if count != 1 else ''}."
        elif any(word in query_lower for word in ['revenue', 'financial', 'money']):
            return f"Generated financial report with {count} data point{'s' if count != 1 else ''}."
        else:
            return f"Retrieved {count} result{'s' if count != 1 else ''} for your query."
    
    def _build_result_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Build expected result schemas for different query types."""
        return {
            "property_search": {
                "required_fields": ["room_id", "room_number", "building_name"],
                "optional_fields": ["private_room_rent", "status", "sq_footage"]
            },
            "analytics": {
                "required_fields": ["metric_name", "metric_value"],
                "optional_fields": ["time_period", "building_name"]
            },
            "tenant_management": {
                "required_fields": ["tenant_id", "tenant_name"],
                "optional_fields": ["status", "room_id", "payment_status"]
            }
        }
