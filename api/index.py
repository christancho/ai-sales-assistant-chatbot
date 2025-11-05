import os
from dotenv import load_dotenv

# Load environment variables early and fail fast if critical secrets are missing.
load_dotenv()
if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError(
        "OPENAI_API_KEY environment variable not set.\n"
        "Please copy .env.example to .env and set OPENAI_API_KEY before starting the server."
    )

from fastapi import FastAPI, HTTPException, Response, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import uuid
from chatbot import chat

app = FastAPI(title="AI Sales Assistant Chatbot API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
    session_id: str
    sources: List[Dict] = []

# In-memory session storage
sessions = {}

# Create API router with /api prefix for Vercel deployment
# For local development, routes are at root level
api_router = APIRouter()

# Explicit OPTIONS handler (if needed)
@api_router.options("/chat")
async def chat_options():
    return Response(status_code=200)

@api_router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Chat endpoint for web widget"""
    # Get or create session
    session_id = request.session_id or str(uuid.uuid4())
    if session_id not in sessions:
        sessions[session_id] = []
    # Get response
    try:
        response_text, updated_history = chat(
            request.message,
            sessions[session_id],
            session_id
        )
        sessions[session_id] = updated_history
        return ChatResponse(
            message=response_text,
            session_id=session_id,
            sources=[]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/health")
async def health_check():
    return {"status": "healthy"}

# Include router with /api prefix for production, and also at root for local dev
app.include_router(api_router, prefix="/api")
app.include_router(api_router)  # Also include at root level for backward compatibility

# Note: No uvicorn.run() block here. Vercel will use the exported 'app'.
