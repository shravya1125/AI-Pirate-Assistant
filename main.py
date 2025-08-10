
import os
import sys
import tempfile
import logging
import shutil
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse
from pydub import AudioSegment
import httpx


from dotenv import load_dotenv
import os

env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path, override=True)

load_dotenv()

def require_env(key: str):
    value = os.getenv(key)
    if not value or value.strip() == "" or value.strip() == "your_api_key_here":
        print(f"❌ ERROR: {key} is missing or invalid. Please set it in .env")
        sys.exit(1)
    return value

ASSEMBLYAI_API_KEY = require_env("ASSEMBLYAI_API_KEY")
GEMINI_API_KEY = require_env("GEMINI_API_KEY")
MURF_API_KEY = require_env("MURF_API_KEY")
# Optional keys (not required for current pipeline)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# --------------------------
# Logging setup
# --------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")


from dotenv import load_dotenv
import os

env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path, override=True)
import os
os.environ["PATH"] += os.pathsep + r"D:\Users\user\ffmpeg-7.1.1-essentials_build\bin"

from pydub import AudioSegment
AudioSegment.converter = r"D:\Users\user\ffmpeg-7.1.1-essentials_build\bin\ffmpeg.exe"
AudioSegment.ffprobe = r"D:\Users\user\ffmpeg-7.1.1-essentials_build\bin\ffprobe.exe"

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import logging
import os

import os
import time
import requests
import assemblyai as aai
import google.generativeai as genai
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# API keys
MURF_API_KEY = os.getenv("MURF_API_KEY")
aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI()

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def get_homepage():
    return FileResponse("static/index.html", media_type="text/html")

# Serve root-level static assets used by the UI
@app.get("/script.js")
def get_script_js():
    return FileResponse("script.js", media_type="application/javascript")


@app.get("/styles.css")
def get_styles_css():
    return FileResponse("styles.css", media_type="text/css")

@app.get("/style.css")
def get_style_css():
    return FileResponse("static/style.css", media_type="text/css")



@app.get("/health")
def health_check():
    return {"status": "ok"}


def get_response_from_gemini(prompt: str) -> str:
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini error: {e}")
        return "Sorry, I couldn't process that."

import tempfile

async def generate_murf_audio(text: str, voice_id: str = "en-US-natalie") -> str:
    """Generate TTS audio using Murf API and return an audio URL/base64 data URL.

    Implements multiple fallback attempts for header and payload variations to handle
    differences across Murf deployments. Falls back to gTTS if Murf fails.
    """
    # Trim excessively long text for TTS safety
    if len(text) > 3000:
        text = text[:2950] + "..."

    murf_api_url = "https://api.murf.ai/v1/speech/generate"

    async def attempt_request(headers: dict, payload: dict) -> tuple[bool, str | dict]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(murf_api_url, headers=headers, json=payload)
        if resp.status_code == 200:
            try:
                return True, resp.json()
            except Exception:
                return False, resp.text
        return False, (resp.json() if 'application/json' in resp.headers.get('content-type', '') else resp.text)

    # Variants to try: Authorization vs api-key header, and voiceId vs voice payload
    payload_voice_id = {
        "text": text,
        "voiceId": voice_id,
        "format": "mp3",
        "speed": 1.0,
        "pitch": 1.0,
        "volume": 1.0,
        "pauseAfter": 0,
        "encodeAsBase64": False,
    }
    payload_voice = {**payload_voice_id}
    payload_voice.pop("voiceId", None)
    payload_voice["voice"] = voice_id

    header_auth = {
        "Authorization": f"Bearer {MURF_API_KEY}",
        "Content-Type": "application/json",
    }
    header_api_key = {
        "api-key": MURF_API_KEY,
        "Content-Type": "application/json",
    }

    attempts: list[tuple[dict, dict]] = [
        (header_auth, payload_voice_id),
        (header_auth, payload_voice),
        (header_api_key, payload_voice_id),
        (header_api_key, payload_voice),
    ]

    last_error: str | None = None
    for headers, payload in attempts:
        try_ok, data = await attempt_request(headers, payload)
        if try_ok:
            result = data  # type: ignore[assignment]
            audio_url = (
                result.get("audioFile")
                or result.get("url")
                or result.get("audioUrl")
            )
            if audio_url:
                return audio_url
            # Base64 variants
            audio_data = result.get("audioData") or result.get("audioBase64")
            if audio_data:
                return f"data:audio/mp3;base64,{audio_data}"
            last_error = f"Unexpected Murf response: {result}"
        else:
            last_error = f"Murf request failed with: {data}"

    # Fallback: gTTS local generation to keep UX working
    try:
        from gtts import gTTS
        import io
        import base64

        tts = gTTS(text=text, lang="en", slow=False)
        buffer = io.BytesIO()
        tts.write_to_fp(buffer)
        buffer.seek(0)
        b64 = base64.b64encode(buffer.read()).decode("utf-8")
        return f"data:audio/mp3;base64,{b64}"
    except Exception as gtts_error:
        raise HTTPException(status_code=502, detail=f"Murf TTS failed. Fallback gTTS also failed: {gtts_error}. Last Murf error: {last_error}")

@app.post("/llm/query")
async def llm_query(
    file: UploadFile = File(...),
    voice_id: str = Form(default="en-US-natalie"),
):
    """Audio -> Transcription -> LLM -> Murf TTS -> Return audioFile URL."""
    content_type = file.content_type or ""
    if not content_type.startswith("audio/") and content_type != "application/octet-stream":
        raise HTTPException(status_code=400, detail=f"Invalid file type: {content_type}")

    tmp_path = None
    try:
        # Save uploaded audio to a temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        # Transcribe using AssemblyAI SDK directly from file path
        config = aai.TranscriptionConfig(
            speaker_labels=False,
            punctuate=True,
            format_text=True,
            language_code="en",
        )
        transcriber = aai.Transcriber(config=config)
        transcript = transcriber.transcribe(tmp_path)

        if transcript.status == aai.TranscriptStatus.error:
            raise HTTPException(status_code=500, detail=f"Transcription failed: {transcript.error}")

        transcription_text = transcript.text or ""
        if not transcription_text.strip():
            raise HTTPException(status_code=400, detail="No speech detected in the audio file")

        # Get LLM response
        llm_response_text = get_response_from_gemini(transcription_text)
        if not llm_response_text:
            llm_response_text = "I'm sorry, I couldn't generate a response. Please try again."

        # Generate Murf audio
        audio_url = await generate_murf_audio(llm_response_text, voice_id)

        return JSONResponse(
            content={
                "success": True,
                "transcription": transcription_text,
                "llm_response": llm_response_text,
                "audioFile": audio_url,
                "voice_id": voice_id,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM query pipeline failed: {e}")
    finally:
        try:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass