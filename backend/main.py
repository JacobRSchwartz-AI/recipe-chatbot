from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn
import logging
import json
import asyncio
from dotenv import load_dotenv

# Import our models and graph
from schemas.models import ChatMessage, ChatResponse, StreamingChatMessage
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

@app.post("/api/chat/stream")
async def chat_stream_endpoint(message: StreamingChatMessage):
    """
    Streaming chat endpoint that returns Server-Sent Events.
    """
    async def generate_stream():
        try:
            logger.info(f"Starting streaming chat for message: {message.message}")
            
            # Send initial status
            yield f"data: {json.dumps({'type': 'status', 'data': 'Processing your request...'})}\n\n"
            
            # Run the LangGraph workflow
            recipe_graph = get_recipe_graph()
            
            # Since the graph doesn't support streaming yet, we'll simulate it
            # by yielding updates at key points and then the final result
            yield f"data: {json.dumps({'type': 'status', 'data': 'Analyzing your cooking question...'})}\n\n"
            await asyncio.sleep(0.1)  # Small delay for UX
            
            # Run the graph
            result = recipe_graph.run(message.message)
            
            # Send tool usage updates
            if result.get("tools_used"):
                for tool in result["tools_used"]:
                    tool_message = f"Using {tool} tool..."
                    yield f"data: {json.dumps({'type': 'tool', 'data': tool_message})}\n\n"
                    await asyncio.sleep(0.1)
            
            # Send cookware check status if available
            if result.get("cookware_check"):
                cookware_status = "Checking available cookware..."
                yield f"data: {json.dumps({'type': 'status', 'data': cookware_status})}\n\n"
                await asyncio.sleep(0.1)
            
            # Send final response in chunks for streaming effect
            response_text = result["response"]
            if response_text:
                yield f"data: {json.dumps({'type': 'status', 'data': 'Generating response...'})}\n\n"
                await asyncio.sleep(0.1)
                
                # Simulate streaming by sending response in chunks
                words = response_text.split()
                current_chunk = ""
                
                for i, word in enumerate(words):
                    current_chunk += word + " "
                    
                    # Send chunk every 5-8 words or at the end
                    if (i + 1) % 6 == 0 or i == len(words) - 1:
                        # For final chunk, strip trailing space; for others, keep it
                        chunk_to_send = current_chunk.rstrip() if i == len(words) - 1 else current_chunk
                        yield f"data: {json.dumps({'type': 'content', 'data': chunk_to_send})}\n\n"
                        current_chunk = ""
                        await asyncio.sleep(0.05)  # Small delay between chunks
            
            # Send final metadata
            final_data = {
                "type": "complete",
                "data": {
                    "is_cooking_related": result["is_cooking_related"],
                    "tools_used": result["tools_used"],
                    "cookware_check": result.get("cookware_check"),
                    "debug_info": result.get("debug_info")
                }
            }
            yield f"data: {json.dumps(final_data)}\n\n"
            
            logger.info("Streaming chat completed successfully")
            
        except Exception as e:
            logger.error(f"Error in streaming chat endpoint: {e}")
            error_data = {
                "type": "error",
                "data": f"Internal server error: {str(e)}"
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
