"""
Query classifier tool to determine if a query is cooking-related.
Uses LangChain LLM for classification.
"""

import os
import logging
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)

class QueryClassifier:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.1,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
    def classify_query(self, query: str) -> Dict[str, Any]:
        """
        Classify if a query is cooking/recipe related.
        
        Args:
            query: User's input query
            
        Returns:
            Dict with classification result and reasoning
        """
        try:
            system_prompt = """You are a query classifier for a cooking chatbot. 
            Determine if the user's query is related to cooking, recipes, food preparation, ingredients, or kitchen activities.
            
            Respond with ONLY a JSON object in this exact format:
            {
                "is_cooking_related": true/false,
                "confidence": 0.0-1.0,
                "reasoning": "brief explanation"
            }
            
            Examples of cooking-related queries:
            - "How do I make scrambled eggs?"
            - "What can I cook with chicken and rice?"
            - "Recipe for chocolate chip cookies"
            - "How long should I boil pasta?"
            
            Examples of non-cooking queries:
            - "What's the weather like?"
            - "Tell me about programming"
            - "How do I fix my car?"
            """
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Query: {query}")
            ]
            
            response = self.llm(messages)
            result_text = response.content.strip()
            
            # Parse the JSON response
            import json
            try:
                result = json.loads(result_text)
                logger.info(f"Query classification: {result}")
                return result
            except json.JSONDecodeError:
                logger.error(f"Failed to parse classification response: {result_text}")
                # Fallback - assume it's cooking related if we can't parse
                return {
                    "is_cooking_related": True,
                    "confidence": 0.5,
                    "reasoning": "Failed to parse classification, defaulting to cooking-related"
                }
                
        except Exception as e:
            logger.error(f"Error in query classification: {e}")
            return {
                "is_cooking_related": True,
                "confidence": 0.5,
                "reasoning": f"Classification error: {str(e)}"
            }

# Global instance will be created when first accessed
_query_classifier = None

def get_query_classifier():
    """Get or create the query classifier instance."""
    global _query_classifier
    if _query_classifier is None:
        _query_classifier = QueryClassifier()
    return _query_classifier
