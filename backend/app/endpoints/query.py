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
    # user_context = query_request.get("user_context", {})
    user_context = {
        "permissions": ["admin"],
        "role": "admin",
        "user_id": query_request.get("user_id", "admin_user")
    }
        
    if not query:
        raise HTTPException(status_code=400, detail="Query text is required.")

    print(f"Received User Query: {query}")
    print(f"User Context: {user_context}") 

    # Use LLM to intelligently select the function (no db parameter needed)
    result = intelligent_function_selection(query,user_context)
    
    logger.info(f"🎯 Function execution result: {result}")
    
    return result

@router.post("/lead-query/", response_model=Dict[str, Any])
async def process_lead_query(query_request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process queries from leads with restricted table access.
    Same as /query/ but automatically sets lead permissions.
    """
    query = query_request.get("query")
    lead_id = query_request.get("lead_id", "anonymous_lead")
    
    # Force lead-specific context
    user_context = {
        "permissions": ["lead"],
        "role": "lead",
        "user_id": lead_id
    }
    
    if not query:
        raise HTTPException(status_code=400, detail="Query text is required.")

    print(f"🔍 Lead Query Endpoint - Query: {query}")
    print(f"🔍 Lead Query Endpoint - User Context: {user_context}")
    print(f"🔍 Lead Query Endpoint - Permissions: {user_context.get('permissions')}")


    # Use LLM to intelligently select the function
    result = intelligent_function_selection(query, user_context)
    
    logger.info(f"🎯 Lead query execution result: {result}")
    
    return result

@router.post("/query/web", response_model=Dict[str, Any])
async def process_web_query(query_request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process query for web interface display with rich formatting.
    Uses intelligent function selection like the main qsuery endpoint.
    """
    query = query_request.get("query")
    user_context = query_request.get("user_context", {})
    
    if not query:
        raise HTTPException(status_code=400, detail="Query text is required.")

    logger.info(f"🌐 Web Query - Query: {query}")
    logger.info(f"🌐 Web Query - User Context: {user_context}")

    try:
        # Use intelligent function selection with format_type
        result = intelligent_function_selection(
            query, 
            user_context,
            format_type="web"  # Pass format_type to function selector
        )
        
        logger.info(f"✅ Web query processed successfully")
        
        return result
    except Exception as e:
        logger.error(f"❌ Web query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query/email", response_model=Dict[str, Any])
async def process_email_query(query_request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process query for email delivery with email-friendly formatting.
    Uses intelligent function selection like the main query endpoint.
    """
    query = query_request.get("query")
    user_context = query_request.get("user_context", {})
    
    if not query:
        raise HTTPException(status_code=400, detail="Query text is required.")

    logger.info(f"📧 Email Query - Query: {query}")
    logger.info(f"📧 Email Query - User Context: {user_context}")

    try:
        # Use intelligent function selection with format_type
        result = intelligent_function_selection(
            query,
            user_context,
            format_type="email"  # Pass format_type to function selector
        )
        
        logger.info(f"✅ Email query processed successfully")
        
        return result
    except Exception as e:
        logger.error(f"❌ Email query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query/sms", response_model=Dict[str, Any])
async def process_sms_query(query_request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process query for SMS delivery with ultra-concise formatting.
    Uses intelligent function selection like the main query endpoint.
    """
    query = query_request.get("query")
    user_context = query_request.get("user_context", {})
    
    if not query:
        raise HTTPException(status_code=400, detail="Query text is required.")

    logger.info(f"📱 SMS Query - Query: {query}")
    logger.info(f"📱 SMS Query - User Context: {user_context}")

    try:
        # Use intelligent function selection with format_type
        result = intelligent_function_selection(
            query,
            user_context,
            format_type="sms"  # Pass format_type to function selector
        )
        
        logger.info(f"✅ SMS query processed successfully")
        
        # Add SMS-specific metadata
        if result.get("response"):  # Check if response exists
            result.setdefault("metadata", {})
            result["metadata"]["character_count"] = len(result.get("response", ""))
            result["metadata"]["sms_parts"] = (len(result.get("response", "")) + 159) // 160
        
        return result
    except Exception as e:
        logger.error(f"❌ SMS query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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