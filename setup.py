import os
import secrets

def setup():
    if os.path.exists(".env"):
        print(".env already exists. Skipping.")
        return

    config = {
        "AI_PROVIDER": input("Enter AI Provider (openai/anthropic/gemini/openrouter): "),
        "AI_API_KEY": input("Enter LLM API Key: "),
        "DAILY_API_KEY": input("Enter Daily.co API Key: "),
        "CARTESIA_API_KEY": input("Enter Cartesia API Key: "),
        "DATABASE_URL": "postgresql://postgres:password@db:5432/meta_db",
        "REDIS_URL": "redis://redis:6379/0",
        "SECRET_KEY": secrets.token_hex(32)
    }

    with open(".env", "w") as f:
        for k, v in config.items():
            f.write(f"{k}={v}\n")
    print("Project Meta configured successfully.")

if __name__ == "__main__":
    setup()
