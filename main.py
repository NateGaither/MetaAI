import os
import httpx
import asyncio
from fastapi import FastAPI, WebSocket, Request
from dotenv import load_dotenv
from redis import Redis
from pipecat.transports.services.small_webrtc import SmallWebRTCTransport
from pipecat.pipeline.pipeline import Pipeline
from pipecat.services.openai import OpenAILLMService
from pipecat.services.cartesia import CartesiaTTSService

# Load configuration from setup.py's .env
load_dotenv()

app = FastAPI()
redis_client = Redis(host='localhost', port=6379, db=0, decode_responses=True)

INSTRUCTIONS_FILE = "instructions.txt"
GITHUB_TEMPLATE_URL = "https://raw.githubusercontent.com/pipecat-ai/pipecat/main/examples/prompts/default-assistant.txt"

# --- 1. BOOTSTRAP: AI INSTRUCTIONS ---
def load_ai_instructions():
    if not os.path.exists(INSTRUCTIONS_FILE):
        print(f"📂 {INSTRUCTIONS_FILE} not found. Fetching from GitHub...")
        try:
            response = httpx.get(GITHUB_TEMPLATE_URL)
            response.raise_for_status()
            with open(INSTRUCTIONS_FILE, "w") as f:
                f.write(response.text)
            print("✅ Instructions created successfully.")
        except Exception as e:
            print(f"❌ Failed to fetch instructions: {e}")
            return "You are Meta, a helpful AI assistant."
    
    with open(INSTRUCTIONS_FILE, "r") as f:
        return f.read()

SYSTEM_PROMPT = load_ai_instructions()

# --- 2. PIPECAT AI PIPELINE ---
async def start_meta_engine(session_id: str, user_id: str):
    # Initialize the "Brain" and "Voice" from .env settings
    llm = OpenAILLMService(api_key=os.getenv("AI_API_KEY"), model="gpt-4o")
    tts = CartesiaTTSService(api_key=os.getenv("CARTESIA_API_KEY"), voice_id="pro-voice-id")
    
    # Define Transport (WebRTC)
    transport = SmallWebRTCTransport()

    # Meta's Memory Retrieval (Simplified logic for pgvector)
    # user_pref = postgres_db.query_memory(user_id) 
    
    pipeline = Pipeline([
        transport.input(),
        llm,
        tts,
        transport.output()
    ])

    # Save session state to Redis so other devices can find this pipeline
    redis_client.setex(f"meta_session:{user_id}", 3600, session_id)
    
    await pipeline.run()

# --- 3. WEB-SERVER & SIGNALING ---
@app.post("/connect")
async def handle_connection(request: Request):
    """
    Signaling endpoint: Clients call this to get a WebRTC configuration.
    It checks Redis to see if the user has an existing conversation to resume.
    """
    data = await request.json()
    user_id = data.get("user_id", "anonymous")
    
    # SESSION CACHE: Check Redis for an existing ID
    active_session = redis_client.get(f"meta_session:{user_id}")
    
    if active_session:
        print(f"🔄 Resuming existing session {active_session} for user {user_id}")
        return {"session_id": active_session, "status": "resuming"}

    # NEW SESSION: Create a unique ID
    new_session_id = f"meta_{user_id}_{os.urandom(4).hex()}"
    
    # Start the AI pipeline in the background
    asyncio.create_task(start_meta_engine(new_session_id, user_id))
    
    return {
        "session_id": new_session_id,
        "status": "started",
        "instructions_version": "v1.0-github-sync"
    }

@app.get("/admin/instructions")
async def view_instructions():
    """Webserver feature: Read the current instructions via API"""
    with open(INSTRUCTIONS_FILE, "r") as f:
        return {"content": f.read()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
