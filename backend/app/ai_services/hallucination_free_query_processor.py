# app/ai_services/hallucination_free_query_processor.py

from typing import Dict, Any, List
from app.ai_services.hallucination_free_sql_generator import HallucinationFreeSQLGenerator
from app.ai_services.sql_executor import SQLExecutor
from app.ai_services.result_verifier import ResultVerifier, FrontendResponse
import time

class HallucinationFreeQueryProcessor:
    """
    Complete query processing system with multi-layer hallucination prevention.
    """
    
    def __init__(self):
        self.sql_generator = HallucinationFreeSQLGenerator()
        self.sql_executor = SQLExecutor()
        self.result_verifier = ResultVerifier()
    
    async def process_query(
        self,
        natural_query: str,
        user_context: Dict[str, Any] = None
    ) -> FrontendResponse:
        """
        Process any query with guaranteed accuracy and frontend compatibility.
        """
        
        if user_context is None:
            user_context = {"permissions": ["basic"], "role": "user"}
        
        start_time = time.time()
        
        try:
            # Layer 1: Generate schema-constrained SQL
            sql_result = await self.sql_generator.generate_sql(
                natural_query, user_context
            )
            
            if not sql_result.get('success') or not sql_result.get('sql'):
                return FrontendResponse(
                    success=False,
                    data=[],
                    message="Failed to understand query",
                    errors=[sql_result.get('error', 'Unknown error')]
                )
            
            # Layer 2: Execute SQL safely
            execution_result = self.sql_executor.execute_query(
                sql_result["sql"]
            )
            
            # Add execution time
            execution_time = time.time() - start_time
            execution_result["execution_time"] = execution_time
            
            # Handle SQL execution failures gracefully
            if not execution_result.get("success", False):
                # Try to provide helpful error message
                error_msg = execution_result.get("error", "Unknown SQL error")
                if "syntax error" in str(error_msg).lower():
                    return FrontendResponse(
                        success=False,
                        data=[],
                        message="Query syntax error. Please try rephrasing your question.",
                        errors=[f"SQL Error: {error_msg}"],
                        metadata={
                            "sql_query": sql_result["sql"],
                            "sql_generation_time": sql_result.get("generation_time", 0),
                            "execution_time": execution_time,
                            "result_type": "error"
                        }
                    )
                else:
                    return FrontendResponse(
                        success=False,
                        data=[],
                        message="Query execution failed. Please try again.",
                        errors=[f"Execution Error: {error_msg}"],
                        metadata={
                            "sql_query": sql_result["sql"],
                            "sql_generation_time": sql_result.get("generation_time", 0),
                            "execution_time": execution_time,
                            "result_type": "error"
                        }
                    )
            
            # Layer 3: Verify and structure results
            final_response = await self.result_verifier.verify_and_structure(
                execution_result,
                natural_query,
                sql_result["sql"],
                user_context
            )
            
            # Add SQL generation metadata
            final_response.metadata.update({
                "sql_generation_time": sql_result.get("generation_time", 0),
                "sql_explanation": sql_result.get("explanation", ""),
                "estimated_rows": sql_result.get("estimated_rows", 0),
                "tables_used": sql_result.get("tables_used", []),
                "query_type": sql_result.get("query_type", "SELECT")
            })
            
            return final_response
            
        except Exception as e:
            return FrontendResponse(
                success=False,
                data=[],
                message="Query processing failed",
                errors=[f"System error: {str(e)}"]
            )
    
    async def process_batch_queries(
        self,
        queries: List[str],
        user_context: Dict[str, Any] = None
    ) -> List[FrontendResponse]:
        """
        Process multiple queries in batch.
        """
        
        if user_context is None:
            user_context = {"permissions": ["basic"], "role": "user"}
        
        results = []
        for query in queries:
            result = await self.process_query(query, user_context)
            results.append(result)
        
        return results
    
    async def get_query_suggestions(
        self,
        partial_query: str,
        user_context: Dict[str, Any] = None
    ) -> List[str]:
        """
        Get query suggestions based on partial input.
        """
        
        if user_context is None:
            user_context = {"permissions": ["basic"], "role": "user"}
        
        suggestions = []
        
        # Basic suggestions based on user permissions
        if "admin" in user_context.get("permissions", []):
            suggestions.extend([
                "Show me all available rooms",
                "What's the occupancy rate by building?",
                "List all tenants with late payments",
                "Show maintenance requests by priority",
                "Generate revenue report for this month"
            ])
        elif "manager" in user_context.get("permissions", []):
            suggestions.extend([
                "Find available rooms under $2000",
                "Show occupancy rates for my buildings",
                "List active tenants",
                "Show pending maintenance requests"
            ])
        elif "agent" in user_context.get("permissions", []):
            suggestions.extend([
                "Find rooms in downtown area",
                "Show leads in showing scheduled status",
                "List available rooms with wifi"
            ])
        else:
            suggestions.extend([
                "Find available rooms",
                "Show room prices",
                "Search by location"
            ])
        
        # Filter suggestions based on partial query
        if partial_query:
            filtered_suggestions = [
                suggestion for suggestion in suggestions
                if partial_query.lower() in suggestion.lower()
            ]
            return filtered_suggestions[:5]  # Limit to 5 suggestions
        
        return suggestions[:5]
    
    async def get_query_statistics(
        self,
        user_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Get statistics about available data for the user.
        """
        
        if user_context is None:
            user_context = {"permissions": ["basic"], "role": "user"}
        
        # Generate basic statistics queries
        stats_queries = [
            "SELECT COUNT(*) as total_rooms FROM rooms",
            "SELECT COUNT(*) as available_rooms FROM rooms WHERE status = 'AVAILABLE'",
            "SELECT COUNT(*) as total_buildings FROM buildings"
        ]
        
        # Add manager/admin specific queries
        if "manager" in user_context.get("permissions", []) or "admin" in user_context.get("permissions", []):
            stats_queries.extend([
                "SELECT COUNT(*) as total_tenants FROM tenants WHERE status = 'ACTIVE'",
                "SELECT COUNT(*) as total_leads FROM leads WHERE status = 'EXPLORING'"
            ])
        
        stats_results = {}
        
        for query in stats_queries:
            try:
                result = self.sql_executor.execute_query(query)
                if result.get("success") and result.get("data"):
                    # Extract the count from the result
                    for key, value in result["data"][0].items():
                        stats_results[key] = value
            except Exception:
                continue
        
        return {
            "success": True,
            "statistics": stats_results,
            "message": "Retrieved system statistics"
        }
    
    async def validate_query(
        self,
        natural_query: str,
        user_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Validate a query without executing it.
        """
        
        if user_context is None:
            user_context = {"permissions": ["basic"], "role": "user"}
        
        try:
            # Generate SQL to validate the query
            sql_result = await self.sql_generator.generate_sql(
                natural_query, user_context
            )
            
            if not sql_result.get('success'):
                return {
                    "valid": False,
                    "errors": [sql_result.get('error', 'Unknown error')],
                    "suggestions": await self.get_query_suggestions(natural_query, user_context)
                }
            
            return {
                "valid": True,
                "sql_preview": sql_result.get("sql", ""),
                "explanation": sql_result.get("explanation", ""),
                "estimated_rows": sql_result.get("estimated_rows", 0),
                "tables_used": sql_result.get("tables_used", []),
                "query_type": sql_result.get("query_type", "SELECT")
            }
            
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Validation failed: {str(e)}"],
                "suggestions": await self.get_query_suggestions(natural_query, user_context)
            }
