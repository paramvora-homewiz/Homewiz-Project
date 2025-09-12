# app/ai_services/update_handler.py

from typing import Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor
from app.ai_services.supabase_update_processor import SupabaseUpdateProcessor

async def update_function(query: str, user_context: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
    """
    Update function that uses SupabaseUpdateProcessor for native updates.
    Returns same format as universal_query_function.
    """
    # Get user_context from kwargs if not directly provided
    if user_context is None and "user_context" in kwargs:
        user_context = kwargs["user_context"]
    
    if user_context is None:
        user_context = {"permissions": ["basic"], "role": "user"}
    
    try:
        # Use SupabaseUpdateProcessor (native Supabase calls)
        processor = SupabaseUpdateProcessor()
        result = await processor.process_update(query, user_context)
        
        # Convert FrontendResponse to dict (matching universal_query_function format)
        return {
            "success": result.success,
            "response": result.message,  # Note: "response" not "message" for compatibility
            "data": result.data,
            "metadata": result.metadata,
            "errors": result.errors,
            "warnings": result.warnings
        }
        
    except Exception as e:
        return {
            "success": False,
            "response": f"Update operation failed: {str(e)}",
            "error": str(e),
            "data": [],
            "errors": [str(e)],
            "warnings": []
        }


def update_function_sync(query: str, user_context: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
    """
    Synchronous wrapper for the async update_function.
    Fixed to work without nest_asyncio.
    """
    try:
        # Handle user_context from kwargs
        if user_context is None and "user_context" in kwargs:
            user_context = kwargs["user_context"]
        
        # Run async function in a thread pool to avoid event loop conflicts
        def run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(update_function(query, user_context, **kwargs))
            finally:
                loop.close()
        
        with ThreadPoolExecutor() as executor:
            future = executor.submit(run_async)
            return future.result()
        
    except Exception as e:
        return {
            "success": False,
            "response": f"Update function error: {str(e)}",
            "error": str(e),
            "data": [],
            "errors": [str(e)],
            "warnings": []
        }