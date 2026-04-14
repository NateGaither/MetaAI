import os
import asyncio
import secrets
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from redis import asyncio as aioredis
from dotenv import load_dotenv

from pipecat.transports.services.daily import DailyTransport, DailyParams
from pipecat.services.openai import OpenAILLMService
from pipecat.services.anthropic import AnthropicLLMService
from pipecat.services.cartesia import CartesiaTTSService
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.processors.aggregators.llm_response import LLMUserResponseAggregator

from utils import fetch_instructions, get_system_prompt
from database import update_user_preference

# Load environment variables
load_dotenv()

app = FastAPI(title="Project Meta AI")

# Initialize Redis connection
redis = aioredis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

class ConnectRequest(BaseModel):
    user_id: str

@app.on_event("startup")
async def startup_event():
    """Ensure system instructions are ready before accepting connections."""
    await fetch_instructions()

def get_llm_service():
    """Factory to select the LLM provider defined in .env."""
    provider = os.getenv("AI_PROVIDER", "openai").lower()
    api_key = os.getenv("AI_API_KEY")
    
    if provider == "anthropic":
        return AnthropicLLMService(api_key=api_key)
    # Defaulting to OpenAI for robustness
    return OpenAILLMService(api_key=api_key)

async def run_meta_pipeline(room_url: str, token: str):
    """
    The core Pipecat pipeline logic.
    Orchestrates real-time audio transport, LLM processing, and TTS.
    """
    transport = DailyTransport(
        room_url,
        token,
        "Meta Assistant",
        DailyParams(
            audio_out_enabled=True, 
            transcription_enabled=True,
            vad_enabled=True # Enable Voice Activity Detection for interruptions
        )
    )

    llm = get_llm_service()
    
    tts = CartesiaTTSService(
        api_key=os.getenv("CARTESIA_API_KEY"),
        voice_id="79a125e8-cd45-4c13-8a25-276b30c5dd0b" # Expressive British Male
    )

    # Register the user preference tool so Meta can call it
    llm.register_function("update_user_preference", update_user_preference)

    messages = [{"role": "system", "content": get_system_prompt()}]
    
    # Context aggregator manages history and handles interruptions mid-speech
    user_response = LLMUserResponseAggregator(messages)
    
    pipeline = Pipeline([
        transport.input(),     # 1. Listen (WebRTC)
        user_response,         # 2. Process Context
        llm,                   # 3. Think (LLM)
        tts,                   # 4. Speak (Cartesia)
        transport.output()     # 5. Output (WebRTC)
    ])

    runner = PipelineRunner()
    await runner.run(pipeline)

@app.post("/connect")
async def connect(request: ConnectRequest):
    """
    Main signaling endpoint. 
    Implements Hub-and-Spoke session continuity via Redis.
    """
    user_id = request.user_id
    
    # 1. Check for existing session (Cross-device handoff)
    session_id = await redis.get(f"session:{user_id}")
    
    if session_id:
        session_id = session_id.decode()
        room_url = await redis.get(f"room:{session_id}")
        if room_url:
            return {
                "room_url": room_url.decode(), 
                "session_id": session_id,
                "status": "resumed"
            }

    # 2. Create new session if none exists
    new_session_id = secrets.token_hex(8)
    daily_key = os.getenv("DAILY_API_KEY")
    
    # Initialize Daily Transport to create a temporary room
    transport = DailyTransport(api_key=daily_key)
    try:
        # Create a room with a 60-minute expiry for security
        room_url = await transport.create_room(params={"properties": {"exp": 3600}})
        token = await transport.create_token(room_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create WebRTC room: {str(e)}")

    # 3. Persist session state in Redis
    await redis.set(f"session:{user_id}", new_session_id, ex=3600)
    await redis.set(f"room:{new_session_id}", room_url, ex=3600)
    
    # 4. Spawn the AI Pipeline in the background
    asyncio.create_task(run_meta_pipeline(room_url, token))
    
    return {
        "room_url": room_url, 
        "session_id": new_session_id, 
        "status": "initialized"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
