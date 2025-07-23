# app/endpoints/query.py
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
import logging

# Import Supabase version
from app.ai_services.intelligent_function_dispatcher_supabase import intelligent_function_selection

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/query/", response_model=Dict[str, Any])
def process_query(query_request: Dict[str, str]) -> Dict[str, Any]:
    """
    Process a natural language query using intelligent LLM function selection.
    Now uses Supabase client instead of SQLAlchemy.
    """
    query = query_request.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="Query text is required.")

    print(f"Received User Query: {query}")

    # Use LLM to intelligently select the function (no db parameter needed)
    result = intelligent_function_selection(query)
    
    logger.info(f"🎯 Function execution result: {result}")
    
    return result