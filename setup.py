import os
import secrets
import httpx

# Configuration Constants
INSTRUCTIONS_FILE = "instructions.txt"
DEFAULT_PROMPT_URL = "https://raw.githubusercontent.com/pipecat-ai/pipecat/main/examples/common/system_prompt.txt"

DEFAULT_SYSTEM_PROMPT = """You are Meta, a centralized, real-time AI Voice Assistant.
Your goal is to provide helpful, concise, and expressive verbal responses.
You support multi-device session continuity and persistent memory.
When the user shares a preference, use the 'update_user_preference' tool to save it."""

def create_instructions():
    """
    Bootstrapping Logic: Checks for instructions.txt locally.
    If missing, attempts to fetch from GitHub or writes a hardcoded default.
    """
    if os.path.exists(INSTRUCTIONS_FILE):
        print(f"[-] {INSTRUCTIONS_FILE} already exists. Skipping download.")
        return

    print(f"[*] Creating {INSTRUCTIONS_FILE}...")
    try:
        # Attempt to fetch the latest default prompt
        response = httpx.get(DEFAULT_PROMPT_URL, timeout=5.0)
        if response.status_code == 200:
            content = response.text
        else:
            content = DEFAULT_SYSTEM_PROMPT
    except Exception:
        # Fallback to hardcoded prompt if offline or URL is down
        content = DEFAULT_SYSTEM_PROMPT

    with open(INSTRUCTIONS_FILE, "w") as f:
        f.write(content)
    print(f"[+] Instructions saved to {INSTRUCTIONS_FILE}")

def run_wizard():
    """
    Interactive CLI to generate a .env file for Project Meta.
    """
    print("--- Project Meta Setup Wizard ---")
    
    if os.path.exists(".env"):
        overwrite = input("[!] .env file already exists. Overwrite? (y/n): ").lower()
        if overwrite != 'y':
            print("[-] Setup aborted.")
            return

    # Collect API Keys and Preferences
    config = {
        "AI_PROVIDER": input("Enter LLM Provider (openai/anthropic/gemini): ") or "openai",
        "AI_API_KEY": input("Enter LLM API Key: "),
        "DAILY_API_KEY": input("Enter Daily.co API Key (WebRTC): "),
        "CARTESIA_API_KEY": input("Enter Cartesia API Key (TTS): "),
        "DATABASE_URL": "postgresql://postgres:password@db:5432/meta_db",
        "REDIS_URL": "redis://redis:6379/0",
        "SECRET_KEY": secrets.token_hex(32)
    }

    # Write to .env
    with open(".env", "w") as f:
        for key, value in config.items():
            f.write(f"{key}={value}\n")
    
    print("[+] .env file generated successfully.")

def main():
    # 1. Create the system prompt instructions
    create_instructions()
    
    # 2. Run the environment configuration wizard
    run_wizard()
    
    print("\n[!] Setup Complete. You can now run 'docker-compose up'.")

if __name__ == "__main__":
    main()
