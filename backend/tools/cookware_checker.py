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
            
            Respond with ONLY a JSON object in this exact format:
            {{
                "can_make": true/false,
                "required_items": ["item1", "item2"],
                "available_items": ["item1", "item2"],
                "missing_items": ["item1", "item2"],
                "confidence": 0.0-1.0,
                "suggestions": "Brief suggestions for alternatives or modifications",
                "reasoning": "Brief explanation of the analysis"
            }}
            """
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Recipe to analyze: {recipe_content}")
            ]
            
            response = self.llm(messages)
            result_text = response.content.strip()
            
            # Parse the JSON response
            import json
            try:
                result = json.loads(result_text)
                logger.info(f"Cookware check completed: can_make={result.get('can_make', False)}")
                return result
            except json.JSONDecodeError:
                logger.error(f"Failed to parse cookware check response: {result_text}")
                # Fallback response
                return {
                    "can_make": True,
                    "required_items": [],
                    "available_items": self.available_cookware,
                    "missing_items": [],
                    "confidence": 0.5,
                    "suggestions": "Unable to analyze cookware requirements",
                    "reasoning": "Failed to parse analysis response"
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
