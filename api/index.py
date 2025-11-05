from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import uuid
from chatbot import chat

app = FastAPI(title="Boralio Chatbot API")

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

# Explicit OPTIONS handler (if needed)
@app.options("/chat")
async def chat_options():
    return Response(status_code=200)

@app.post("/chat", response_model=ChatResponse)
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

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Note: No uvicorn.run() block here. Vercel will use the exported 'app'.
