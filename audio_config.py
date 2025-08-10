# config.py
from dotenv import load_dotenv
import os
import sys

load_dotenv()

def require_env(key: str):
    value = os.getenv(key)
    if not value or value.strip() == "" or value.strip() == "your_api_key_here":
        print(f"❌ ERROR: {key} is missing or invalid. Please set it in .env")
        sys.exit(1)
    return value

ASSEMBLYAI_API_KEY = require_env("ASSEMBLYAI_API_KEY")
GEMINI_API_KEY     = require_env("GEMINI_API_KEY")
MURF_API_KEY       = require_env("MURF_API_KEY")
