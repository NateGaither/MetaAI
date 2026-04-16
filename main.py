import os
import glob
import importlib
import json
from fastapi import FastAPI
from pipecat.transports.network.small_webrtc import SmallWebRTCTransport
from pipecat.services.whisper import FasterWhisperSTTService
from pipecat.services.kokoro import KokoroTTSService
from pipecat.services.openai import OpenAILLMService
from pipecat.pipeline.pipeline import Pipeline
from pipecat.processors.aggregators.llm_response import LLMUserResponseAggregator

app = FastAPI()

def load_plugins(llm):
    """Dynamic Tool Discovery: Scans /plugins folders."""
    for p in glob.glob("plugins/*/plugin.py"):
        module_name = p.replace("/", ".").replace(".py", "")
        module = importlib.import_module(module_name)
        # Assuming plugin has a 'config' dict for tool schema
        llm.register_tool(module.config, module.execute)

async def start_meta(user_id: str):
    # Sovereign Transport (No Daily.co)
    transport = SmallWebRTCTransport() 
    
    # Local-Only Engine URLs (Docker Internal)
    stt = FasterWhisperSTTService(url="http://stt:8000")
    tts = KokoroTTSService(url="http://tts:8000")
    
    llm = OpenAILLMService(
        api_key=os.getenv("AI_API_KEY"),
        base_url="https://openrouter.ai/api/v1"
    )
    
    load_plugins(llm) # Dynamic plugin registration

    # Pipeline: Audio In -> STT -> Thresholded Memory -> LLM -> TTS -> Audio Out
    pipeline = Pipeline([
        transport.input(),
        stt,
        LLMUserResponseAggregator([]), # Context management
        llm,
        tts,
        transport.output()
    ])
    
    await pipeline.run()

@app.post("/connect")
async def connect(user_id: str):
    # Redis session verification logic here
    import asyncio
    asyncio.create_task(start_meta(user_id))
    return {"status": "handshaking"}
