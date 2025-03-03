# app/endpoints/query.py
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..services import query_service
from ..db.connection import get_db

router = APIRouter()

@router.post("/query/", response_model=Dict[str, Any]) # Define response model as Dict for now
def process_query(query_request: Dict[str, str], db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Process a natural language query using the AI query engine.
    """
    query = query_request.get("query") # Expecting query to be sent in a JSON like {"query": "your question"}
    if not query:
        raise HTTPException(status_code=400, detail="Query text is required in the request body.")

    query_result = query_service.process_query(db=db, query=query)
    return query_result