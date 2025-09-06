# app/ai_services/update_verifier.py

from typing import Dict, Any, List
from app.ai_services.result_verifier import FrontendResponse

class UpdateVerifier:
    """
    Verifies and structures update results for frontend compatibility.
    """
    
    def create_response(
        self,
        execution_result: Dict[str, Any],
        update_spec: Dict[str, Any]
    ) -> FrontendResponse:
        """
        Create a standardized FrontendResponse from update results.
        
        Args:
            execution_result: Result from SupabaseUpdateExecutor
            update_spec: Original update specification
            
        Returns:
            FrontendResponse object
        """
        
        if not execution_result.get("success"):
            return FrontendResponse(
                success=False,
                data=[],
                message=f"Update failed: {execution_result.get('error', 'Unknown error')}",
                errors=[execution_result.get('error', 'Unknown error')],
                metadata={
                    "table": update_spec.get("table"),
                    "attempted_update": update_spec.get("update_data"),
                    "where_conditions": update_spec.get("where_conditions"),
                    "preview_count": execution_result.get("preview_count", 0)
                }
            )
        
        # Success response
        row_count = execution_result.get("row_count", 0)
        table = update_spec.get("table")
        explanation = update_spec.get("explanation", "Update completed")
        
        # Generate user-friendly message
        if row_count == 0:
            message = "No records were updated (no matching records found)"
        elif row_count == 1:
            message = f"Successfully updated 1 record in {table}"
        else:
            message = f"Successfully updated {row_count} records in {table}"
        
        # Add explanation if available
        if explanation and explanation != "Update completed":
            message = f"{message}. {explanation}"
        
        return FrontendResponse(
            success=True,
            data=execution_result.get("data", []),
            message=message,
            metadata={
                "table": table,
                "update_data": update_spec.get("update_data"),
                "where_conditions": update_spec.get("where_conditions"),
                "row_count": row_count,
                "operation": "UPDATE",
                "explanation": explanation,
                "generation_time": update_spec.get("generation_time", 0)
            }
        )
    
    def create_validation_error_response(
        self,
        error_message: str,
        update_spec: Dict[str, Any] = None
    ) -> FrontendResponse:
        """Create error response for validation failures."""
        
        return FrontendResponse(
            success=False,
            data=[],
            message="Update validation failed",
            errors=[error_message],
            metadata={
                "attempted_spec": update_spec
            } if update_spec else {}
        )