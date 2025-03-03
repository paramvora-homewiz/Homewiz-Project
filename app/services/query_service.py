# app/services/query_service.py
from typing import Dict, Any

from sqlalchemy.orm import Session

# Assuming UnifiedQueryEngine is moved to app.services.ai.query_engine
# If not, adjust the import path accordingly
from ..services.ai.query_engine import UnifiedQueryEngine, UserRole

# Initialize the query engine - you might want to configure the db_path dynamically
query_engine = UnifiedQueryEngine(db_path='homewiz_management.db', role=UserRole.LEAD) # Or determine role dynamically if needed

def process_query(db: Session, query: str) -> Dict[str, Any]:
    """
    Processes a natural language query using the UnifiedQueryEngine.
    """
    result = query_engine.process_query(query)
    # Convert QueryResult to a dictionary for FastAPI response
    return {
        "response": result.response,
        "data": result.data.to_dict(orient='records') if result.data is not None and hasattr(result.data, 'to_dict') else result.data, #Pandas DataFrame to dict
        "context": result.context,
        "status": result.status,
        "metadata": result.metadata
    }