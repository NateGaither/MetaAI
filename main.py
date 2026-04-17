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
    transport = SmallWebRTCTransport() 
    
    stt = FasterWhisperSTTService(url="http://stt:8000")
    
    # Corrected TTS Config
    tts = KokoroTTSService(url="http://tts:8880/v1", voice="af_sky")

    llm = OpenAILLMService(
        api_key=os.getenv("AI_API_KEY"),
        base_url="https://openrouter.ai/api/v1"
    )
    
    # 1. Define initial context (Brain initialization)
    messages = [{"role": "system", "content": "You are Meta, a sovereign AI."}]
    user_response = LLMUserResponseAggregator(messages)

    # 2. Add Plugin Registration logic (with error handling)
    try:
        load_plugins(llm)
    except Exception as e:
        print(f"Plugin load failed: {e}")

    # 3. Optimized Pipeline Flow
    pipeline = Pipeline([
        transport.input(),     # Mic
        stt,                   # Audio -> Text
        user_response,         # Text Aggregator
        llm,                   # Text -> AI Text
        tts,                   # AI Text -> Audio
        transport.output()     # Speaker
    ])
    
    from pipecat.pipeline.runner import PipelineRunner
    runner = PipelineRunner()
    await runner.run(pipeline)

@app.post("/connect")
async def connect(user_id: str):
    # Redis session verification logic here
    import asyncio
    asyncio.create_task(start_meta(user_id))
    return {"status": "handshaking"}
