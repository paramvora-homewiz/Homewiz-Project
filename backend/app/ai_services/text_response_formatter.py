# app/ai_services/text_response_formatter.py

import json
from typing import Dict, Any, List
from google import genai
from app.config import GEMINI_API_KEY
from google.genai.types import GenerateContentConfig

class TextResponseFormatter:
    """Formats query results for text/email delivery using LLM"""
    
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)
    
    async def format_response(
        self,
        data: List[Dict[str, Any]],
        original_query: str,
        result_type: str
    ) -> str:
        """
        Generate a natural, conversational response suitable for text/email.
        
        Args:
            data: The query results
            original_query: The user's original question
            result_type: Type of query (property_search, analytics, etc.)
            
        Returns:
            Formatted string response
        """
        
        # Limit data for prompt (to stay within token limits)
        sample_data = data[:5] if len(data) > 5 else data
        
        # Build the prompt
        prompt = f"""
        Generate a natural, conversational response for this real estate query result:
        
        Original Query: "{original_query}"
        Query Type: {result_type}
        Number of Results: {len(data)}
        
        Data Sample:
        {json.dumps(sample_data, indent=2)}
        
        CRITICAL FORMATTING RULES:
        - Use simple ASCII characters that work everywhere:
        - Bullet points: * or -
        - Headers: Plain text followed by colon
        - No Unicode/emojis/dividers in content
        - Use line breaks strategically for readability
        - Align data with pipes | for easy scanning

        Guidelines:
        * Be conversational and helpful
        * Highlight key information (prices, locations, availability)
        * Format numbers nicely (e.g., $1,500 not 1500)
        * Include only essential information first
        * Add detailed breakdowns after main summary
        * If multiple results, summarize key insights
        * Keep response under 500 words
        * Be specific about what was found
        * Professional but friendly tone
        * Don't Suggest any actions at end of response. Just provide information. 

        FORMATTING EXAMPLES:
        Property Search:
        SUMMARY: Found 5 available rooms from $1,200-$2,000 in Downtown area
        
        Details:
        * 1080 Folsom - Room 101
        Rent: $1,200/mo | Available Now | 150 sq ft
        
        * 1080 Folsom - Room 205  
        Rent: $1,500/mo | Available Dec 1 | 200 sq ft
        
        Analytics:
        SUMMARY: Building occupancy at 73% with $45K potential revenue from vacant units
        
        Building Breakdown:
        * 1080 Folsom: 85% occupied (38/45 rooms)
        * 221 7th Street: 62% occupied (8/13 rooms)
        
        Revenue Impact:
        Total Vacant: 20 rooms
        Potential Revenue: $45,000/month
        
        Update Operations:
        SUMMARY: Successfully updated Room 101 status to Occupied
        
        Update Details:
        * Table: rooms
        * Changed: status from 'Available' to 'Occupied'
        * Affected: 1 record
        
        Example responses:
        * For room search: "I found 5 available rooms matching your criteria! The prices range from $1,200 to $1,800..."
        * For statistics: "Here's what I found in our database: We have 45 total rooms with 12 currently available..."
        * For updates: "Successfully updated the room status. Room 101 is now marked as occupied."
        """
        
        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=prompt,
                config=GenerateContentConfig(
                    temperature=0.5,
                    # max_output_tokens=300
                )
            )
            
            return response.text.strip()
            
        except Exception as e:
            # Fallback to simple message if LLM fails
            return self._generate_fallback_message(data, original_query, result_type)
    
    def _generate_fallback_message(
        self,
        data: List[Dict[str, Any]],
        original_query: str,
        result_type: str
    ) -> str:
        """Generate a simple fallback message if LLM fails"""
        
        count = len(data)
        
        if count == 0:
            return "No results found for your query."
        elif result_type == "property_search":
            return f"Found {count} property{'ies' if count != 1 else ''} matching your search."
        elif result_type == "analytics":
            return f"Retrieved {count} data point{'s' if count != 1 else ''} for your analysis."
        elif result_type == "update":
            return "Update completed successfully."
        else:
            return f"Found {count} result{'s' if count != 1 else ''} for your query."