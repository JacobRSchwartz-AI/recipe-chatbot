from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ChatMessage(BaseModel):
    message: str
    user_id: Optional[str] = "default"

class ChatResponse(BaseModel):
    response: str
    is_cooking_related: bool
    tools_used: List[str] = []
    cookware_check: Optional[Dict[str, Any]] = None
    debug_info: Optional[Dict[str, Any]] = None

class CookwareItem(BaseModel):
    name: str
    available: bool = True

# Hardcoded cookware list from requirements
AVAILABLE_COOKWARE = [
    "Spatula",
    "Frying Pan", 
    "Little Pot",
    "Stovetop",
    "Whisk",
    "Knife",
    "Ladle",
    "Spoon"
]
