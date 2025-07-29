"""
Cookware checker tool to validate recipes against available cookware.
Uses LangChain LLM to analyze recipe requirements.
"""

import os
import logging
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from schemas.models import AVAILABLE_COOKWARE

logger = logging.getLogger(__name__)

class CookwareChecker:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.1,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        self.available_cookware = AVAILABLE_COOKWARE
        
    def check_recipe_feasibility(self, recipe_content: str) -> Dict[str, Any]:
        """
        Check if a recipe can be made with available cookware.
        
        Args:
            recipe_content: Recipe instructions or description
            
        Returns:
            Dict with feasibility analysis
        """
        try:
            available_items = ", ".join(self.available_cookware)
            
            system_prompt = f"""You are a cooking assistant analyzing recipe feasibility.
            
            Available cookware and tools:
            {available_items}
            
            Analyze the provided recipe and determine:
            1. What cookware/tools are required
            2. Whether the recipe can be made with available items
            3. What items are missing (if any)
            4. Suggested alternatives or modifications
            
            CRITICAL: You must respond with ONLY a valid JSON object. Do not include any markdown, explanations, or other text.
            
            Use this EXACT format (copy exactly):
            {{
                "can_make": true,
                "required_items": ["item1", "item2"],
                "available_items": ["item1", "item2"],
                "missing_items": [],
                "confidence": 0.8,
                "suggestions": "Brief suggestions for alternatives or modifications",
                "reasoning": "Brief explanation of the analysis"
            }}
            
            Replace the values appropriately but keep the exact structure and field names.
            The confidence should be a number between 0.0 and 1.0.
            """
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Recipe to analyze: {recipe_content}")
            ]
            
            response = self.llm(messages)
            result_text = response.content.strip()
            
            # Parse the JSON response with better error handling
            import json
            import re
            
            try:
                # First, try to parse directly
                result = json.loads(result_text)
                
                # Validate that the result has the expected structure
                required_fields = ["can_make", "required_items", "available_items", "missing_items", "confidence", "suggestions", "reasoning"]
                if all(field in result for field in required_fields):
                    # Ensure lists are actually lists
                    for list_field in ["required_items", "available_items", "missing_items"]:
                        if not isinstance(result[list_field], list):
                            result[list_field] = []
                    
                    # Ensure confidence is a number between 0 and 1
                    if not isinstance(result["confidence"], (int, float)) or not (0 <= result["confidence"] <= 1):
                        result["confidence"] = 0.5
                    
                    # Ensure can_make is boolean
                    if not isinstance(result["can_make"], bool):
                        result["can_make"] = True
                    
                    logger.info(f"Cookware check completed: can_make={result.get('can_make', False)}")
                    return result
                else:
                    logger.error(f"Parsed JSON missing required fields. Got: {list(result.keys())}")
                    raise json.JSONDecodeError("Missing required fields", result_text, 0)
                    
            except json.JSONDecodeError:
                # If direct parsing fails, try to extract JSON from the response
                logger.warning(f"Direct JSON parsing failed. Attempting to extract JSON from: {result_text[:200]}...")
                
                # Look for JSON object in the response using regex
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    try:
                        json_text = json_match.group(0)
                        result = json.loads(json_text)
                        logger.info(f"Successfully extracted JSON from response: can_make={result.get('can_make', False)}")
                        return result
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse extracted JSON: {json_text[:200]}")
                
                # If all parsing attempts fail, log the full response and return fallback
                logger.error(f"Complete response that failed to parse: {result_text}")
                return {
                    "can_make": True,
                    "required_items": [],
                    "available_items": self.available_cookware,
                    "missing_items": [],
                    "confidence": 0.5,
                    "suggestions": "Unable to analyze cookware requirements - response parsing failed",
                    "reasoning": f"Failed to parse LLM response as JSON. Response: {result_text[:100]}..."
                }
                
        except Exception as e:
            logger.error(f"Error in cookware check: {e}")
            return {
                "can_make": True,
                "required_items": [],
                "available_items": self.available_cookware,
                "missing_items": [],
                "confidence": 0.3,
                "suggestions": f"Error during analysis: {str(e)}",
                "reasoning": f"Analysis failed: {str(e)}"
            }
    
    def get_cookware_summary(self, cookware_result: Dict[str, Any]) -> str:
        """
        Create a human-readable summary of cookware analysis.
        
        Args:
            cookware_result: Result from check_recipe_feasibility
            
        Returns:
            Formatted summary string
        """
        can_make = cookware_result.get("can_make", False)
        missing_items = cookware_result.get("missing_items", [])
        suggestions = cookware_result.get("suggestions", "")
        
        if can_make:
            summary = "✅ **Good news!** You can make this recipe with your available cookware."
        else:
            summary = "⚠️ **Heads up!** This recipe requires some cookware you don't have."
            
        if missing_items:
            summary += f"\n\n**Missing items:** {', '.join(missing_items)}"
            
        if suggestions:
            summary += f"\n\n**Suggestions:** {suggestions}"
            
        return summary

# Global instance will be created when first accessed
_cookware_checker = None

def get_cookware_checker():
    """Get or create the cookware checker instance."""
    global _cookware_checker
    if _cookware_checker is None:
        _cookware_checker = CookwareChecker()
    return _cookware_checker
