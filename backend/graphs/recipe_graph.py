"""
LangGraph workflow for the recipe chatbot.
Implements the main decision-making engine with conditional routing.
"""

import os
import logging
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from typing import TypedDict

# Import our tools
from tools.query_classifier import get_query_classifier
from tools.web_search import get_web_search_tool
from tools.cookware_checker import get_cookware_checker

logger = logging.getLogger(__name__)

class RecipeState(TypedDict):
    """State for the recipe chatbot workflow."""
    user_message: str
    is_cooking_related: bool
    classification_result: Dict[str, Any]
    web_search_results: Dict[str, Any]
    cookware_check_result: Dict[str, Any]
    final_response: str
    tools_used: List[str]
    debug_info: Dict[str, Any]

class RecipeGraph:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.3,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        self.graph = self._build_graph()
        
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(RecipeState)
        
        # Add nodes
        workflow.add_node("classify_query", self.classify_query_node)
        workflow.add_node("handle_non_cooking", self.handle_non_cooking_node)
        workflow.add_node("decide_tools", self.decide_tools_node)
        workflow.add_node("web_search", self.web_search_node)
        workflow.add_node("cookware_check", self.cookware_check_node)
        workflow.add_node("generate_response", self.generate_response_node)
        
        # Set entry point
        workflow.set_entry_point("classify_query")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "classify_query",
            self.should_proceed_with_cooking,
            {
                "cooking": "decide_tools",
                "non_cooking": "handle_non_cooking"
            }
        )
        
        workflow.add_conditional_edges(
            "decide_tools",
            self.which_tools_to_use,
            {
                "web_search": "web_search",
                "cookware_only": "cookware_check",
                "both": "web_search",
                "neither": "generate_response"
            }
        )
        
        workflow.add_conditional_edges(
            "web_search",
            self.should_check_cookware,
            {
                "yes": "cookware_check",
                "no": "generate_response"
            }
        )
        
        # Terminal edges
        workflow.add_edge("handle_non_cooking", END)
        workflow.add_edge("cookware_check", "generate_response")
        workflow.add_edge("generate_response", END)
        
        return workflow.compile()
    
    def classify_query_node(self, state: RecipeState) -> RecipeState:
        """Node to classify if query is cooking-related."""
        logger.info(f"Classifying query: {state['user_message']}")
        
        query_classifier = get_query_classifier()
        classification = query_classifier.classify_query(state["user_message"])
        
        state["classification_result"] = classification
        state["is_cooking_related"] = classification.get("is_cooking_related", False)
        state["debug_info"] = {"classification": classification}
        
        return state
    
    def handle_non_cooking_node(self, state: RecipeState) -> RecipeState:
        """Handle non-cooking related queries."""
        logger.info("Handling non-cooking query")
        
        state["final_response"] = (
            "I'm a cooking and recipe assistant! I'd be happy to help you with "
            "cooking questions, recipe suggestions, ingredient substitutions, "
            "cooking techniques, or meal planning. What would you like to cook today?"
        )
        state["tools_used"] = []
        
        return state
    
    def decide_tools_node(self, state: RecipeState) -> RecipeState:
        """Decide which tools to use based on the query."""
        logger.info("Deciding which tools to use")
        
        user_message = state["user_message"].lower()
        
        # Simple heuristics for tool selection
        needs_web_search = any(keyword in user_message for keyword in [
            "recipe for", "how to make", "how do i", "recipe", "instructions"
        ])
        
        # For cooking-related queries, always check cookware unless explicitly asking about something else
        needs_cookware_check = True  # Default to always checking cookware for cooking queries
        
        # Only skip cookware check for very specific non-cooking or informational queries
        skip_cookware_keywords = [
            "what is", "define", "explain", "tell me about", "history of", 
            "nutrition", "calories", "where does", "when was", "who invented"
        ]
        
        if any(keyword in user_message for keyword in skip_cookware_keywords):
            needs_cookware_check = False
        
        # Default to web search for most cooking queries if no specific tool trigger
        if not needs_web_search and needs_cookware_check:
            needs_web_search = True
            
        state["debug_info"]["tool_decisions"] = {
            "needs_web_search": needs_web_search,
            "needs_cookware_check": needs_cookware_check
        }
        
        logger.info(f"Tool decisions: web_search={needs_web_search}, cookware_check={needs_cookware_check}")
        
        return state
    
    def web_search_node(self, state: RecipeState) -> RecipeState:
        """Perform web search for recipe information."""
        logger.info("Performing web search")
        
        web_search_tool = get_web_search_tool()
        search_results = web_search_tool.search_recipes(state["user_message"])
        state["web_search_results"] = search_results
        state["tools_used"] = state.get("tools_used", []) + ["web_search"]
        
        return state
    
    def cookware_check_node(self, state: RecipeState) -> RecipeState:
        """Check cookware requirements."""
        logger.info("Checking cookware requirements")
        
        # Use web search results if available, otherwise use original query
        recipe_content = state["user_message"]
        if state.get("web_search_results", {}).get("success"):
            # Combine search results for analysis
            results = state["web_search_results"]["results"]
            if results:
                recipe_content = " ".join([
                    result.get("title", "") + " " + result.get("snippet", "")
                    for result in results[:2]  # Use top 2 results
                ])
        
        cookware_checker = get_cookware_checker()
        cookware_result = cookware_checker.check_recipe_feasibility(recipe_content)
        state["cookware_check_result"] = cookware_result
        state["tools_used"] = state.get("tools_used", []) + ["cookware_check"]
        
        return state
    
    def generate_response_node(self, state: RecipeState) -> RecipeState:
        """Generate the final response using LLM."""
        logger.info("Generating final response")
        
        try:
            # Prepare context for response generation
            context_parts = []
            
            if state.get("web_search_results", {}).get("success"):
                web_search_tool = get_web_search_tool()
                search_summary = web_search_tool.get_recipe_summary(
                    state["web_search_results"]["results"]
                )
                context_parts.append(f"Web search results:\n{search_summary}")
            
            if state.get("cookware_check_result"):
                cookware_checker = get_cookware_checker()
                cookware_summary = cookware_checker.get_cookware_summary(
                    state["cookware_check_result"]
                )
                context_parts.append(f"Cookware analysis:\n{cookware_summary}")
            
            context = "\n\n".join(context_parts) if context_parts else ""
            
            system_prompt = """You are a helpful cooking assistant. Based on the user's question and any available context from web search and cookware analysis, provide a comprehensive and helpful response.

Guidelines:
- Be friendly and encouraging
- Provide clear, step-by-step instructions when relevant
- Include helpful tips and alternatives
- If cookware analysis shows missing items, suggest alternatives
- Keep responses practical and easy to follow
- Use the provided context to enhance your response

If you have web search results, incorporate the most relevant information.
If you have cookware analysis, address any limitations or suggestions."""
            
            user_prompt = f"""User question: {state['user_message']}

Available context:
{context}

Please provide a helpful cooking response."""
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = self.llm(messages)
            state["final_response"] = response.content
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            state["final_response"] = (
                "I apologize, but I encountered an error while generating your response. "
                "Please try asking your cooking question again!"
            )
        
        return state
    
    # Conditional edge functions
    def should_proceed_with_cooking(self, state: RecipeState) -> str:
        """Decide whether to proceed with cooking logic or handle non-cooking."""
        return "cooking" if state["is_cooking_related"] else "non_cooking"
    
    def which_tools_to_use(self, state: RecipeState) -> str:
        """Decide which tools to use based on the query analysis."""
        debug_info = state.get("debug_info", {})
        tool_decisions = debug_info.get("tool_decisions", {})
        
        needs_web = tool_decisions.get("needs_web_search", False)
        needs_cookware = tool_decisions.get("needs_cookware_check", False)
        
        if needs_web and needs_cookware:
            return "both"
        elif needs_web:
            return "web_search"
        elif needs_cookware:
            return "cookware_only"
        else:
            return "neither"
    
    def should_check_cookware(self, state: RecipeState) -> str:
        """Decide if cookware check is needed after web search."""
        debug_info = state.get("debug_info", {})
        tool_decisions = debug_info.get("tool_decisions", {})
        
        # If we explicitly decided we need cookware check, do it
        if tool_decisions.get("needs_cookware_check", False):
            return "yes"
        
        # For any cooking-related query that went through web search, also check cookware
        # This ensures we almost always check cookware for recipe-related queries
        user_message = state["user_message"].lower()
        
        # Skip cookware check only for very specific informational queries
        skip_cookware_keywords = [
            "what is", "define", "explain", "tell me about", "history of", 
            "nutrition", "calories", "where does", "when was", "who invented"
        ]
        
        if any(keyword in user_message for keyword in skip_cookware_keywords):
            logger.info("Skipping cookware check for informational query")
            return "no"
        
        # Default to yes for all other cooking queries
        logger.info("Including cookware check for recipe/cooking query")
        return "yes"
    
    def run(self, user_message: str) -> Dict[str, Any]:
        """Run the complete workflow for a user message."""
        logger.info(f"Starting workflow for message: {user_message}")
        
        initial_state = RecipeState(
            user_message=user_message,
            is_cooking_related=False,
            classification_result={},
            web_search_results={},
            cookware_check_result={},
            final_response="",
            tools_used=[],
            debug_info={}
        )
        
        try:
            final_state = self.graph.invoke(initial_state)
            
            logger.info(f"Workflow completed. Tools used: {final_state.get('tools_used', [])}")
            
            return {
                "response": final_state.get("final_response", ""),
                "is_cooking_related": final_state.get("is_cooking_related", False),
                "tools_used": final_state.get("tools_used", []),
                "cookware_check": final_state.get("cookware_check_result"),
                "debug_info": final_state.get("debug_info", {})
            }
            
        except Exception as e:
            logger.error(f"Error in workflow execution: {e}")
            return {
                "response": "I apologize, but I encountered an error processing your request. Please try again!",
                "is_cooking_related": False,
                "tools_used": [],
                "cookware_check": None,
                "debug_info": {"error": str(e)}
            }

# Global instance will be created when first accessed
_recipe_graph = None

def get_recipe_graph():
    """Get or create the recipe graph instance."""
    global _recipe_graph
    if _recipe_graph is None:
        _recipe_graph = RecipeGraph()
    return _recipe_graph
