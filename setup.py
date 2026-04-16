import os
import secrets
import httpx
from dotenv import set_key

def bootstrap_instructions():
    """Fetch instructions.txt from GitHub if missing."""
    if not os.path.exists("instructions.txt"):
        url = "https://raw.githubusercontent.com/your-repo/meta/main/instructions.txt"
        resp = httpx.get(url)
        with open("instructions.txt", "w") as f:
            f.write(resp.text)
        print("[+] Instructions downloaded.")

def run_wizard():
    env = ".env"
    if not os.path.exists(env): open(env, 'a').close()
    
    set_key(env, "AI_API_KEY", input("OpenRouter API Key: "))
    set_key(env, "HA_TOKEN", input("Home Assistant Token: "))
    set_key(env, "POSTGRES_PASSWORD", secrets.token_urlsafe(16))
    print("[+] Sovereign environment ready.")

if __name__ == "__main__":
    run_wizard()
    bootstrap_instructions()
