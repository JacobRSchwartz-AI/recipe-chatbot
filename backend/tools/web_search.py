"""
Web search tool using SERP API for recipe research.
"""

import os
import logging
import httpx
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class WebSearchTool:
    def __init__(self):
        self.serp_api_key = os.getenv("SERP_API_KEY")
        if not self.serp_api_key:
            logger.warning("SERP_API_KEY not found in environment variables")
        
    def search_recipes(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """
        Search for recipe information using SERP API.
        
        Args:
            query: Search query related to cooking/recipes
            num_results: Number of search results to return
            
        Returns:
            Dict containing search results and metadata
        """
        if not self.serp_api_key:
            return {
                "success": False,
                "error": "SERP API key not configured",
                "results": []
            }
            
        try:
            # Add cooking-related keywords to improve relevance
            enhanced_query = f"{query} recipe cooking instructions"
            
            params = {
                "q": enhanced_query,
                "num": num_results,
                "api_key": self.serp_api_key,
                "engine": "google"
            }
            
            # Use httpx for async-compatible requests
            with httpx.Client() as client:
                response = client.get("https://serpapi.com/search", params=params)
                response.raise_for_status()
                
                data = response.json()
                
                # Extract organic results
                organic_results = data.get("organic_results", [])
                
                # Format results for better consumption
                formatted_results = []
                for result in organic_results:
                    formatted_result = {
                        "title": result.get("title", ""),
                        "link": result.get("link", ""),
                        "snippet": result.get("snippet", ""),
                        "displayed_link": result.get("displayed_link", "")
                    }
                    formatted_results.append(formatted_result)
                
                logger.info(f"Web search successful for query: {query}")
                return {
                    "success": True,
                    "query": query,
                    "num_results": len(formatted_results),
                    "results": formatted_results
                }
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during web search: {e}")
            return {
                "success": False,
                "error": f"HTTP error: {str(e)}",
                "results": []
            }
        except Exception as e:
            logger.error(f"Error during web search: {e}")
            return {
                "success": False,
                "error": f"Search error: {str(e)}",
                "results": []
            }
    
    def get_recipe_summary(self, search_results: List[Dict[str, Any]]) -> str:
        """
        Create a summary from web search results for recipe information.
        
        Args:
            search_results: List of search result dictionaries
            
        Returns:
            Formatted summary string
        """
        if not search_results:
            return "No web search results available."
            
        summary_parts = []
        summary_parts.append("Here's what I found from web search:")
        summary_parts.append("")
        
        for i, result in enumerate(search_results[:3], 1):  # Limit to top 3
            title = result.get("title", "Unknown Recipe")
            snippet = result.get("snippet", "No description available")
            link = result.get("link", "")
            
            summary_parts.append(f"{i}. **{title}**")
            summary_parts.append(f"   {snippet}")
            if link:
                summary_parts.append(f"   Source: {link}")
            summary_parts.append("")
            
        return "\n".join(summary_parts)

# Global instance will be created when first accessed
_web_search_tool = None

def get_web_search_tool():
    """Get or create the web search tool instance."""
    global _web_search_tool
    if _web_search_tool is None:
        _web_search_tool = WebSearchTool()
    return _web_search_tool
