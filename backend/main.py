from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from dotenv import load_dotenv

# Import our models and graph
from schemas.models import ChatMessage, ChatResponse
from graphs.recipe_graph import get_recipe_graph

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Recipe Chatbot API",
    description="AI-powered cooking and recipe Q&A system",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Recipe Chatbot API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(message: ChatMessage):
    """
    Main chat endpoint that processes user messages through the LangGraph workflow.
    """
    try:
        logger.info(f"Received chat message: {message.message}")
        
        # Run the LangGraph workflow
        recipe_graph = get_recipe_graph()
        result = recipe_graph.run(message.message)
        
        # Create response
        response = ChatResponse(
            response=result["response"],
            is_cooking_related=result["is_cooking_related"],
            tools_used=result["tools_used"],
            cookware_check=result.get("cookware_check"),
            debug_info=result.get("debug_info")
        )
        
        logger.info(f"Chat response generated successfully. Tools used: {result['tools_used']}")
        return response
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
