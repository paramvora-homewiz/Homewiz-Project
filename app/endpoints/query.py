# app/endpoints/query.py
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

# from ..services import query_service
# from app.ai_dispatcher import function_dispatcher
# from app.ai_functions import find_buildings_rooms_function
# from app.ai_services.find_rooms import find_buildings_rooms_function  # Import the function
from app.db.connection import get_db
from app.ai_services.intelligent_function_dispatcher import intelligent_function_selection
from app.config import GEMINI_API_KEY
from google import genai
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()



@router.post("/query/", response_model=Dict[str, Any])
def process_query(query_request: Dict[str, str], db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Process a natural language query using intelligent LLM function selection."""
    
    query = query_request.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="Query text is required.")

    print(f"Received User Query: {query}")

    # Use LLM to intelligently select the function
    result = intelligent_function_selection(query, db)
    
    logger.info(f"🎯 Function execution result: {result}")
    
    return result



