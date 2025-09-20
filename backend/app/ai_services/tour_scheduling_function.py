# app/ai_services/tour_scheduling_function.py

from typing import Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor
from app.ai_services.hallucination_free_query_processor import HallucinationFreeQueryProcessor

# Initialize the processor
tour_processor = HallucinationFreeQueryProcessor()

def tour_scheduling_function(query: str, user_context: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
    """
    Tour scheduling function using the universal hallucination-free processor.
    Handles tour booking, availability checking, and management.
    """
    
    # Get user_context from kwargs if not directly provided
    if user_context is None and "user_context" in kwargs:
        user_context = kwargs["user_context"]
    
    if user_context is None:
        user_context = {
            "user_id": kwargs.get("user_id", "anonymous"),
            "permissions": kwargs.get("permissions", ["basic"]),
            "role": kwargs.get("role", "user")
        }
    
    # Add tour-specific context
    user_context["operation_type"] = "tour_scheduling"
    
    try:
        # Run async function in a thread pool to avoid event loop conflicts
        def run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(tour_processor.process_query(query, user_context))
            finally:
                loop.close()
        
        with ThreadPoolExecutor() as executor:
            future = executor.submit(run_async)
            result = future.result()
        
        # Convert result to expected format
        return {
            "success": result.success,
            "response": result.message,
            "data": result.data,
            "metadata": result.metadata,
            "errors": result.errors,
            "warnings": result.warnings
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Tour scheduling failed: {str(e)}",
            "response": "Failed to process tour request. Please try again.",
            "data": []
        }

# Helper function for quick tour operations
async def quick_tour_check(room_id: str, date: str = None) -> Dict[str, Any]:
    """
    Quick check for tour availability for a specific room.
    """
    if date:
        query = f"Show available tour slots for room {room_id} on {date}"
    else:
        query = f"Show available tour slots for room {room_id} this week"
    
    return tour_scheduling_function(query)