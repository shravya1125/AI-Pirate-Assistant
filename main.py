from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import requests

# Load environment variables
load_dotenv()
MURF_API_KEY = os.getenv("MURF_API_KEY")

app = FastAPI()

# Input model
class TextInput(BaseModel):
    text: str

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# POST endpoint to generate audio
@app.post("/generate-audio")
def generate_audio(input_data: TextInput, voice_id: str = Query(default="en-AU-kylie")):
    if not MURF_API_KEY:
        raise HTTPException(status_code=500, detail="Missing Murf API Key")

    headers = {
        "api-key": MURF_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "text": input_data.text,
        "voice_id": voice_id
    }

    murf_url = "https://api.murf.ai/v1/speech/generate"
    response = requests.post(murf_url, json=payload, headers=headers)

    if response.status_code == 200:
        data = response.json()
        # Return only necessary fields for frontend
        return {
            "audioFile": data.get("audioFile"),
            "warning": data.get("warning", ""),
            "wordDurations": data.get("wordDurations", []),
        }
    else:
        # Return only error message from Murf for clarity
        try:
            error_detail = response.json()
        except Exception:
            error_detail = response.text
        raise HTTPException(status_code=response.status_code, detail=error_detail)

