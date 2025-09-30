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

    def _format_building_link(self, building_name: str, image_url: str = None) -> str:
        """Format building name as hyperlink if URL exists."""
        if image_url and image_url.strip():
            # Escape any quotes in the URL for safety
            safe_url = image_url.replace('"', '&quot;')
            return f'<a href="{safe_url}">{building_name}</a>'
        return building_name
    
    async def format_response(
        self,
        data: List[Dict[str, Any]],
        original_query: str,
        result_type: str,
        format_type: str = "web"
    ) -> str:
        """
        Generate a natural, conversational response suitable for text/email.
        
        Args:
            data: The query results
            original_query: The user's original question
            result_type: Type of query (property_search, analytics, etc.)
            format_type: Output format - "web", "email", or "sms"
            
        Returns:
            Formatted string response
        """
        # Limit data for prompt (to stay within token limits)
        sample_data = data[:5] if len(data) > 5 else data

        # Build format-specific prompts
        if format_type == "email":
            prompt = f"""
            Generate a professional, visually appealing email response for this property management query:

            Original Query: "{original_query}"
            Query Type: {result_type}
            Number of Results: {len(data)}

            Data Sample:
            {json.dumps(sample_data, indent=2)}

            EMAIL FORMATTING REQUIREMENTS:

            PROFESSIONAL STRUCTURE:
            - Start with personalized greeting: "Dear [User/Resident/Team],"
            - Use HTML-friendly formatting that works in all email clients
            - Include a compelling subject line suggestion at the top
            - Professional signature with contact information
            - Keep under 500 words for optimal readability

            IMPORTANT DATA STRUCTURE NOTE:
            - Each result may contain building.image_url or building_image_url
            - Use these URLs to create clickable building name links
            - Room results include: room_number, building_name, and potentially building_image_url
            - Analytics results may include: building_name and building_image_url
            - Always check for the presence of image URL before creating links

            VISUAL ELEMENTS:
            - Use headers with === underlines for sections
            - Bullet points with • for lists
            - Format currency professionally: $1,500/month
            - Bold **important values** using asterisks
            - Create visual separation with line breaks
            - Use tables with | pipes | for data comparison

            HYPERLINK FORMATTING:
            - When displaying building names or "Room X - Building Name", create HTML hyperlinks if building_image_url exists
            - Format: <a href="[building_image_url]">[building_name]</a>
            - If no image URL exists, display plain text
            - Examples:
              * With URL: "<a href='https://example.com/building.jpg'> Room 101 - 1080 Folsom</a>"
              * Without URL: "Room 205 - Sunset Residences"
            - Apply to all building name mentions in the email
            - Ensure proper HTML escaping for security

            CONTENT HIERARCHY:
            Subject: [Suggested subject line based on query]

            Dear User,

            [Warm opening line acknowledging their query]

            === Executive Summary ===
            [1-2 sentence overview of findings]

            === Key Results ===
            [Main findings with essential details]
            • Point 1 with **highlighted value**
            • Point 2 with relevant information
            • Point 3 with actionable insight

            === Detailed Breakdown ===
            [Comprehensive results in organized format]

            === Next Steps ===
            [Any relevant follow-up information]

            Best regards,

            HomeWiz Property Management Team
            📞 (555) 123-4567
            ✉️ info@homewiz.com
            🌐 www.homewiz.com

            EXAMPLES:
            - Subject: "✅ 5 Available Rooms Found Matching Your Criteria"
            - Subject: "📊 October Occupancy Report - 73% Overall"
            - Use warm language: "I'm pleased to share..." or "Great news! We found..."
            """

        elif format_type == "sms":
            prompt = f"""
            Generate an ultra-concise SMS response that maximizes information density:

            Original Query: "{original_query}"
            Query Type: {result_type}
            Number of Results: {len(data)}

            Data Sample:
            {json.dumps(sample_data, indent=2)}

            📱 SMS CRITICAL CONSTRAINTS:

            ⚡ HARD LIMITS:
            - MAXIMUM 160 chars for single SMS (count every character!)
            - If multiple parts needed, use (1/2), (2/2) format
            - Each part must be ≤153 chars (7 chars for headers)

            ✂️ ABBREVIATION GUIDE:
            - Rooms/Properties: rm, apt, bldg, fl (floor), BR (bedroom), BA (bathroom)
            - Money: $1.2k (not $1,200), $45k, $1.5M
            - Status: avail, occup, maint, pend
            - Locations: dwntwn, SOMA, FiDi (Financial District)
            - Time: ASAP, mo (month), wk (week), 12/1 (dates)

            📊 INFORMATION PRIORITY:
            1. Answer the core question first
            2. Include numbers/counts
            3. Top 2-3 most relevant details only
            4. Price and location are critical
            5. Skip all pleasantries

            🎯 FORMAT TEMPLATES:

            Property Search:
            "[#] rms found. [Rm#] - $[building_images_url] $[price]/[area], [Rm#] $[price]/[area]. [Key amenity]"

            Analytics:
            "[Metric]:[value]. [Bldg1]:[%], [Bldg2]:[%]. [Key insight]"

            Status Updates:
            "[Action] done. [What changed]: [old]→[new]. [Impact]"

            REAL EXAMPLES (with char count):
            - "3 rms avail. #101 $1.2k/SOMA, #205 $1.5k/FiDi. All w/WiFi+gym. Reply INFO for more" (84 chars)
            - "Occup:73%. 1080F:85%, 221-7th:62%. $45k/mo potential from 20 vacant" (69 chars)
            - "Updated: 5 rms→occup. Bldg avg now 78%. Rev +$6k/mo" (53 chars)

            ⚠️ NEVER:
            - Use greetings/closings
            - Include "HomeWiz" or company name
            - Add punctuation unless essential
            - Use complete sentences if fragments work
            """

        else:  # format_type == "web" (default)
            prompt = f"""
            Create a structured response optimized for a React-based web UI that will parse and render this data:
            
            Original Query: "{original_query}"
            Query Type: {result_type}
            Number of Results: {len(data)}
            
            Data Sample:
            {json.dumps(sample_data, indent=2)}
            
            REACT UI FORMATTING GUIDELINES:
            
            IMPORTANT: The React frontend will parse and style this response. Focus on:
            - Clean, semantic structure that React components can easily render
            - Logical content hierarchy that maps to component structure
            - Data-focused formatting (the UI will handle the visual styling)
            - Markdown syntax that React-Markdown can parse
            
            MARKDOWN FOR REACT:
            - Use standard markdown headers: # ## ### (React will style these)
            - Bold with **text** and italics with *text*
            - Lists with - or * (React will convert to proper list components)
            - Tables with proper markdown syntax (React-Table compatible)
            - Links: [text](url) format
            - NO HTML tags - only pure markdown
            - NO custom Unicode boxes/borders (React components handle containers)
            - Building links: When building_image_url exists, format as [Building Name](image_url)
            - This allows React to render as clickable links or image previews
            - Example: [1080 Folsom](https://example.com/1080-folsom.jpg)
            
            STRUCTURE FOR REACT COMPONENTS:
            
            # [Clear Page Title]
            
            ## Summary Section
            **Quick Stats:** [Key numbers that a StatsCard component can display]
            - Total Results: count
            - Price Range: $min - $max
            - Availability: [e.g., "5 available now"]
            
            ## Results Section
            
            ### Result Item 1 Title
            **Key Details:**
            - Price: $X,XXX/month
            - Location: [Area/Building Name]
            - Size: XXX sq ft
            - Available: [Date or "Now"]
            
            **Features:**
            - Feature 1
            - Feature 2
            - Feature 3
            
            **Additional Info:**
            [Any extra details in a paragraph format]
            
            ---
            
            [Repeat for each result...]
            
            ## Insights Section
            [Any analytical insights or trends]
            
            📊 DATA TABLES (React-Table Ready):
            
            | Column 1 | Column 2 | Column 3 | Column 4 |
            |----------|----------|----------|----------|
            | Data 1   | Data 2   | Data 3   | Data 4   |
            | Data 1   | Data 2   | Data 3   | Data 4   |
            
            🎯 REACT COMPONENT MAPPING:
            The frontend expects these sections:
            1. Title (h1) - Will render in a PageHeader component
            2. Summary (h2) - Will render in a SummaryCard component  
            3. Results (h2) with items (h3) - Will map to ResultCard components
            4. Tables - Will render in a DataTable component
            5. Insights - Will render in an InsightsPanel component
            
            📱 RESPONSIVE CONSIDERATIONS:
            - Keep text concise (React UI will handle truncation/expansion)
            - Group related data (will render in collapsible cards)
            - Provide clear hierarchical structure
            - Use consistent formatting patterns
            
            ✅ DO:
            - Use clean markdown syntax
            - Provide structured, parseable content
            - Include all relevant data fields
            - Use consistent naming for similar items
            - Format numbers with commas ($1,500 not $1500)
            
            ❌ DON'T:
            - Add visual decorations (emojis/unicode boxes)
            - Include UI instructions ("click here", "scroll down")
            - Use complex formatting (React handles this)
            - Add CSS or styling hints
            - Include interactive elements syntax
            
            EXAMPLE OUTPUT STRUCTURE:
            
            # Available Rooms Report
            
            ## Summary
            **Found:** 5 rooms matching your criteria
            **Price Range:** $1,200 - $2,000 per month
            **Locations:** Downtown (3), SOMA (2)
            
            ## Available Rooms
            
            ### Studio at 1080 Folsom - Room 101
            **Key Details:**
            - Price: $1,200/month
            - Size: 150 sq ft
            - Floor: 1st
            - Available: Now
            
            **Amenities:**
            - High-speed WiFi included
            - Access to fitness center
            - Shared kitchen
            - Laundry on-site
            
            **Location Benefits:**
            Walking distance to BART, surrounded by cafes and restaurants.
            
            ---
            
            ### One Bedroom at 371 Columbus - Room 205
            [Continue pattern...]
            
            ## Market Insights
            These prices are 5% below market average for the area. High demand expected for downtown units.
            
            Remember: The React frontend will transform this markdown into beautiful, interactive components with:
            - Animated cards
            - Interactive filters  
            - Collapsible sections
            - Hover effects
            - Responsive grid layouts
            - Loading skeletons
            - Sort/filter capabilities
            
            Your job is to provide clean, well-structured content that the React components can render beautifully.
            """
                
        # # Build the prompt
        # prompt = f"""
        # Generate a natural, conversational response for this real estate query result:
        
        # Original Query: "{original_query}"
        # Query Type: {result_type}
        # Number of Results: {len(data)}
        
        # Data Sample:
        # {json.dumps(sample_data, indent=2)}
        
        # CRITICAL FORMATTING RULES:
        # - Use simple ASCII characters that work everywhere:
        # - Bullet points: * or -
        # - Headers: Plain text followed by colon
        # - No Unicode/emojis/dividers in content
        # - Use line breaks strategically for readability
        # - Align data with pipes | for easy scanning

        # Guidelines:
        # * Be conversational and helpful
        # * Highlight key information (prices, locations, availability)
        # * Format numbers nicely (e.g., $1,500 not 1500)
        # * Include only essential information first
        # * Add detailed breakdowns after main summary
        # * If multiple results, summarize key insights
        # * Keep response under 500 words
        # * Be specific about what was found
        # * Professional but friendly tone
        # * Don't Suggest any actions at end of response. Just provide information. 

        # FORMATTING EXAMPLES:
        # Property Search:
        # SUMMARY: Found 5 available rooms from $1,200-$2,000 in Downtown area
        
        # Details:
        # * 1080 Folsom - Room 101
        # Rent: $1,200/mo | Available Now | 150 sq ft
        
        # * 1080 Folsom - Room 205  
        # Rent: $1,500/mo | Available Dec 1 | 200 sq ft
        
        # Analytics:
        # SUMMARY: Building occupancy at 73% with $45K potential revenue from vacant units
        
        # Building Breakdown:
        # * 1080 Folsom: 85% occupied (38/45 rooms)
        # * 221 7th Street: 62% occupied (8/13 rooms)
        
        # Revenue Impact:
        # Total Vacant: 20 rooms
        # Potential Revenue: $45,000/month
        
        # Update Operations:
        # SUMMARY: Successfully updated Room 101 status to Occupied
        
        # Update Details:
        # * Table: rooms
        # * Changed: status from 'Available' to 'Occupied'
        # * Affected: 1 record
        
        # Example responses:
        # * For room search: "I found 5 available rooms matching your criteria! The prices range from $1,200 to $1,800..."
        # * For statistics: "Here's what I found in our database: We have 45 total rooms with 12 currently available..."
        # * For updates: "Successfully updated the room status. Room 101 is now marked as occupied."
        # """
        
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
            return self._generate_fallback_message(data, original_query, result_type,format_type)
    
    def _generate_fallback_message(
        self,
        data: List[Dict[str, Any]],
        original_query: str,
        result_type: str,
        format_type: str = "web"
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