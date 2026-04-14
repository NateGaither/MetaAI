import os
import secrets
from pathlib import Path
from dotenv import set_key

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def run_setup():
    clear_screen()
    print("==========================================")
    print("   🌐 META AI VOICE ASSISTANT SETUP   ")
    print("==========================================\n")

    env_path = Path(".env")
    if env_path.exists():
        confirm = input("⚠️  A .env file already exists. Overwrite? (y/N): ")
        if confirm.lower() != 'y':
            print("Setup aborted.")
            return
    else:
        env_path.touch()

    # --- 1. LLM Provider Configuration ---
    print("\n[STEP 1] Choose your AI Brain (LLM)")
    print("1. OpenAI (GPT-4o, GPT-4o-mini)")
    print("2. Anthropic (Claude 3.5 Sonnet)")
    print("3. Google Gemini (1.5 Pro/Flash)")
    print("4. OpenRouter (Llama 3, Mistral, etc.)")
    
    choice = input("\nSelect 1-4 (default 1): ") or "1"
    providers = {"1": "openai", "2": "anthropic", "3": "gemini", "4": "openrouter"}
    selected_provider = providers.get(choice, "openai")
    
    api_key = input(f"Enter your {selected_provider.upper()} API Key: ").strip()
    
    # --- 2. Real-Time Infrastructure ---
    print("\n[STEP 2] Real-Time Voice Infrastructure")
    print("Meta uses Daily.co for low-latency WebRTC audio.")
    daily_key = input("Enter Daily.co API Key: ").strip()
    
    print("\nMeta uses Cartesia for high-speed 'human' speech.")
    cartesia_key = input("Enter Cartesia API Key: ").strip()

    # --- 3. Database & Security ---
    print("\n[STEP 3] System Security")
    # Generate a random secret for the Dashboard session/auth
    flask_secret = secrets.token_hex(16)
    
    # --- 4. Write to .env ---
    set_key(".env", "AI_PROVIDER", selected_provider)
    set_key(".env", "AI_API_KEY", api_key)
    set_key(".env", "DAILY_API_KEY", daily_key)
    set_key(".env", "CARTESIA_API_KEY", cartesia_key)
    set_key(".env", "SECRET_KEY", flask_secret)
    
    # Database defaults for Docker
    set_key(".env", "POSTGRES_DB", "meta_memory")
    set_key(".env", "POSTGRES_USER", "meta_admin")
    set_key(".env", "POSTGRES_PASSWORD", secrets.token_urlsafe(12))
    set_key(".env", "REDIS_URL", "redis://localhost:6379/0")

    print("\n==========================================")
    print("✅ SETUP COMPLETE!")
    print("Your configurations are saved in .env")
    print("\nNext steps:")
    print("1. Run 'docker-compose up -d' to start Redis/Postgres")
    print("2. Run 'python main.py' to launch Meta")
    print("==========================================\n")

if __name__ == "__main__":
    try:
        run_setup()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled.")
