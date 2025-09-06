# app/ai_services/supabase_update_processor.py

import time
from typing import Dict, Any
from app.ai_services.supabase_update_generator import SupabaseUpdateGenerator
from app.ai_services.supabase_update_executor import SupabaseUpdateExecutor
from app.ai_services.update_verifier import UpdateVerifier
from app.ai_services.result_verifier import FrontendResponse

class SupabaseUpdateProcessor:
    """
    Complete update processing system using native Supabase calls.
    Matches the pattern of HallucinationFreeQueryProcessor.
    """
    
    def __init__(self):
        self.generator = SupabaseUpdateGenerator()
        self.executor = SupabaseUpdateExecutor()
        self.verifier = UpdateVerifier()
    
    async def process_update(
        self,
        natural_query: str,
        user_context: Dict[str, Any] = None
    ) -> FrontendResponse:
        """
        Process update query with guaranteed accuracy using native Supabase.
        """
        
        if user_context is None:
            user_context = {"permissions": ["basic"], "role": "user"}
        
        start_time = time.time()
        
        try:
            # Layer 1: Generate Supabase update specification
            generation_result = await self.generator.generate_update_code(
                natural_query, user_context
            )
            
            if not generation_result.get('success'):
                return self.verifier.create_validation_error_response(
                    generation_result.get('error', 'Failed to generate update'),
                    generation_result
                )
            
            update_spec = generation_result
            
            # Layer 2: Validate data types before execution
            if update_spec.get("update_data"):
                validated_data = self.executor.validate_value_types(
                    update_spec["table"],
                    update_spec["update_data"]
                )
                update_spec["update_data"] = validated_data
            
            # Layer 3: Execute update with preview and safety checks
            execution_result = self.executor.execute_update(update_spec)
            
            # Add timing
            execution_result["total_time"] = time.time() - start_time
            
            # Layer 4: Create structured response
            return self.verifier.create_response(execution_result, update_spec)
            
        except Exception as e:
            return FrontendResponse(
                success=False,
                data=[],
                message="Update processing failed",
                errors=[f"System error: {str(e)}"]
            )
    
    async def validate_update(
        self,
        natural_query: str,
        user_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Validate an update without executing it.
        """
        
        if user_context is None:
            user_context = {"permissions": ["basic"], "role": "user"}
        
        try:
            # Generate update specification
            generation_result = await self.generator.generate_update_code(
                natural_query, user_context
            )
            
            if not generation_result.get('success'):
                return {
                    "valid": False,
                    "errors": [generation_result.get('error', 'Unknown error')],
                    "update_spec": None
                }
            
            # Preview what would be updated
            preview_result = self.executor._preview_update(generation_result)
            
            return {
                "valid": True,
                "update_spec": generation_result,
                "preview_count": preview_result.get("count", 0),
                "preview_data": preview_result.get("data", [])[:5],  # First 5 rows
                "explanation": generation_result.get("explanation", "")
            }
            
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Validation failed: {str(e)}"],
                "update_spec": None
            }