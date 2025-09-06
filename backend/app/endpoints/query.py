# app/endpoints/query.py
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
import logging

# Import Supabase version
from app.ai_services.intelligent_function_dispatcher_supabase import intelligent_function_selection
from app.ai_services.hallucination_free_query_processor import HallucinationFreeQueryProcessor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize the universal query processor
universal_processor = HallucinationFreeQueryProcessor()

@router.post("/query/", response_model=Dict[str, Any])
async def process_query(query_request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a natural language query using intelligent LLM function selection.
    Now uses Supabase client instead of SQLAlchemy.
    """
    query = query_request.get("query")
    user_context = query_request.get("user_context", {})
    
    
    if not query:
        raise HTTPException(status_code=400, detail="Query text is required.")

    print(f"Received User Query: {query}")
    print(f"User Context: {user_context}") 

    # Use LLM to intelligently select the function (no db parameter needed)
    result = intelligent_function_selection(query,user_context)
    
    logger.info(f"🎯 Function execution result: {result}")
    
    return result

@router.post("/universal-query/", response_model=Dict[str, Any])
async def process_universal_query(query_request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process any natural language query using the hallucination-free universal processor.
    """
    query = query_request.get("query")
    user_context = query_request.get("user_context", {})
    
    if not query:
        raise HTTPException(status_code=400, detail="Query text is required.")

    print(f"Received Universal Query: {query}")

    # Use the universal query processor
    result = await universal_processor.process_query(query, user_context)
    
    logger.info(f"🎯 Universal query result: {result}")
    
    return {
        "success": result.success,
        "data": result.data,
        "message": result.message,
        "metadata": result.metadata,
        "errors": result.errors,
        "warnings": result.warnings
    }

@router.post("/query/suggestions/", response_model=List[str])
async def get_query_suggestions(suggestion_request: Dict[str, Any]) -> List[str]:
    """
    Get query suggestions based on partial input.
    """
    partial_query = suggestion_request.get("partial_query", "")
    user_context = suggestion_request.get("user_context", {})
    
    suggestions = await universal_processor.get_query_suggestions(partial_query, user_context)
    
    return suggestions

@router.post("/query/validate/", response_model=Dict[str, Any])
async def validate_query(validation_request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a query without executing it.
    """
    query = validation_request.get("query")
    user_context = validation_request.get("user_context", {})
    
    if not query:
        raise HTTPException(status_code=400, detail="Query text is required.")
    
    validation_result = await universal_processor.validate_query(query, user_context)
    
    return validation_result

@router.get("/query/statistics/", response_model=Dict[str, Any])
async def get_query_statistics(user_context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Get statistics about available data for the user.
    """
    if user_context is None:
        user_context = {}
    
    stats_result = await universal_processor.get_query_statistics(user_context)
    
    return stats_result