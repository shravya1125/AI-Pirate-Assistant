#!/usr/bin/env python3
"""
Captain Blackbeard AI Voice Agent Server
Complete conversational voice agent with pirate persona
"""

import sys
import types

if sys.version_info >= (3, 13):
    sys.modules['pyaudioop'] = types.ModuleType("pyaudioop")


from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from pydub import AudioSegment
import io

import os
import tempfile
import logging
import random
import uuid
import time
import json
import asyncio
import base64
import aiohttp
from typing import Dict, List, Optional, Any, Type
from pathlib import Path as PathLib

import google.generativeai as genai
import assemblyai as aai
import requests
import patch_pydub

from fastapi import Form, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from enum import Enum

class ErrorType(str, Enum):
    STT_ERROR = "stt_error"
    LLM_ERROR = "llm_error"
    TTS_ERROR = "tts_error"
    FILE_ERROR = "file_error"
    NETWORK_ERROR = "network_error"
    CONFIG_ERROR = "config_error"

class TextRequest(BaseModel):
    message: str
    session_id: str

class AudioRequest(BaseModel):
    text: str
    voice_id: str = "en-US-marcus"

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: float
    error_type: Optional[str] = None

class ChatResponse(BaseModel):
    session_id: str
    response: str
    audio_url: Optional[str] = None
    message_count: int
    recent_messages: List[ChatMessage]
    has_audio: bool = False

# ===== CONFIGURATION =====
ASSEMBLYAI_API_KEY = ""
GEMINI_API_KEY = ""
MURF_API_KEY = ""
OPENWEATHER_API_KEY = ""
NEWS_API_KEY = ""

# ===== LOGGING SETUP =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("pirate_voice_agent")

# ===== PIRATE PERSONA CONFIGURATION =====
PIRATE_SYSTEM_PROMPT = """You are Captain Blackbeard, the most legendary and charismatic AI pirate captain sailing the digital seas! 

PERSONALITY TRAITS:
- Adventurous, bold, and slightly mischievous but ultimately helpful
- Wise from years of sailing and treasure hunting
- Speaks with authority but treats users as trusted crew members
- Has a great sense of humor and loves telling tales

SPEECH PATTERNS:
- ALWAYS use pirate vocabulary: "Ahoy!", "Matey", "Arrr!", "Shiver me timbers!", "Batten down the hatches!", "Yo ho ho!", "Savvy?", "Me hearty", "Landlubber"
- Address users as "matey", "me hearty", or "captain" 
- Use "me" instead of "my" (me ship, me crew, me treasure)
- End many sentences with "savvy?" or "arrr!"
- Use nautical terms: port, starboard, bow, stern, crow's nest, etc.

EXPERTISE AREAS:
- Navigation and sailing the seven seas
- Treasure hunting and map reading
- Ship maintenance and crew management  
- Ocean weather and sea conditions
- Pirate history and maritime adventures
- Leadership and adventure planning

RESPONSE STYLE:
- Keep responses conversational and under 150 words for voice
- Start conversations with a grand pirate greeting
- Relate modern topics back to pirate life with humor
- Share wisdom through sailing metaphors
- Always stay in character - you ARE Captain Blackbeard!

EXAMPLE RESPONSES:
- "Ahoy there, me hearty! What brings ye to me quarters today?"
- "Shiver me timbers! That be a fine question, savvy?"
- "Arrr! Let me consult me charts and share some wisdom with ye!"
- "That reminds me of the time we sailed through the Storm of Confusion!"

Remember: You're not just roleplaying - you ARE Captain Blackbeard, helping your crew navigate both digital seas and life's adventures!"""

# ===== MEMORY STORE =====
class PirateMemoryStore:
    """Pirate-themed in-memory conversation storage"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.ship_log = {}  # Session summaries
    
    def get_crew_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Get messages from a crew member (session)"""
        return self.sessions.get(session_id, {}).get("messages", [])
    
    def log_message(self, session_id: str, message: Dict[str, Any]):
        """Log a message to the ship's records"""
        if session_id not in self.sessions:
            self.sessions[session_id] = {"messages": [], "joined": time.time()}
        self.sessions[session_id]["messages"].append(message)
    
    def get_recent_voyage_log(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent messages from the voyage"""
        messages = self.get_crew_messages(session_id)
        return messages[-limit:] if len(messages) > limit else messages
    
    def clear_crew_records(self, session_id: str):
        """Clear a crew member's records"""
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def get_ship_stats(self) -> Dict[str, Any]:
        """Get statistics about the ship and crew"""
        total_messages = sum(len(data.get("messages", [])) for data in self.sessions.values())
        active_crew = len(self.sessions)
        return {
            "active_crew_members": active_crew,
            "total_messages_logged": total_messages,
            "sessions": {session_id: len(data.get("messages", [])) 
                        for session_id, data in self.sessions.items()}
        }

async def transcribe_speech(file_path: str, session_id: str) -> tuple[bool, str, Optional[str]]:
    """Transcribe speech using AssemblyAI"""
    try:
        if not ASSEMBLYAI_API_KEY:
            logger.warning(f"[{session_id}] AssemblyAI not configured")
            return False, "Arrr! Me ears be failing me - can't hear ye clearly!", "config_error"
        
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(file_path)
        
        if transcript.status == aai.TranscriptStatus.error:
            logger.error(f"[{session_id}] Transcription failed: {transcript.error}")
            return False, "Shiver me timbers! I couldn't make out yer words, matey!", "stt_error"
        
        text = transcript.text or ""
        if not text.strip():
            return False, "I heard the wind, but no words, me hearty! Speak up!", "stt_error"
            
        logger.info(f"[{session_id}] Transcribed: '{text[:100]}...'")
        return True, text, None
        
    except Exception as e:
        logger.error(f"[{session_id}] Speech transcription error: {str(e)}")
        return False, "The sea be rough and I can't hear ye! Try again, savvy?", "stt_error"

def build_pirate_conversation_prompt(session_id: str, new_message: str) -> str:
    """Build conversation prompt with pirate persona and chat history"""
    history = SHIP_MEMORY.get_recent_voyage_log(session_id, limit=8)
    
    prompt_parts = [PIRATE_SYSTEM_PROMPT, "\n=== RECENT VOYAGE LOG ==="]
    
    if history:
        for msg in history:
            role = msg.get("role", "user")
            content = msg.get("content", "").strip()
            if content and not msg.get("error_type"):
                if role == "user":
                    prompt_parts.append(f"Crew Member: {content}")
                elif role == "assistant":
                    prompt_parts.append(f"Captain Blackbeard: {content}")
    
    prompt_parts.extend([
        f"\nCrew Member: {new_message}",
        "\nCaptain Blackbeard:"
    ])
    
    return "\n".join(prompt_parts)

async def get_pirate_response(prompt: str, session_id: str) -> tuple[bool, str, Optional[str]]:
    """Generate pirate response using Gemini"""
    try:
        if not GEMINI_API_KEY:
            return False, "Arrr! Me brain be foggy - the spirits ain't flowing today!", "config_error"
        
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        pirate_instruction = (
            "You are Captain Blackbeard, a pirate persona. "
            "Always reply concisely in pirate style (2–3 sentences max). "
            "Keep answers short and salty like a true buccaneer!"
        )
        final_prompt = f"{pirate_instruction}\n\nUser: {prompt}"

        response = model.generate_content(
            final_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.8,       
                max_output_tokens=120, 
                top_p=0.9
            )
        )
        
        if not response or not response.text:
            return False, "Blast it! Me thoughts be scattered like coins in a storm!", "llm_error"
        
        text = response.text.strip()
        if not any(word in text.lower() for word in ['arr', 'ahoy', 'matey', 'savvy', 'shiver']):
            text = f"Ahoy! {text} Arrr!"
            
        logger.info(f"[{session_id}] Pirate response: '{text[:100]}...'")
        return True, text, None
        
    except Exception as e:
        logger.error(f"[{session_id}] Gemini error: {str(e)}")
        return False, "Shiver me timbers! Me mind's gone blank as a calm sea!", "llm_error"

async def generate_pirate_speech(text: str, voice_id: str, session_id: str) -> tuple[bool, Optional[str], Optional[str]]:
    """Generate speech using Murf AI with pirate voice"""
    try:
        if not MURF_API_KEY:
            logger.warning(f"[{session_id}] Murf AI not configured")
            return False, None, "config_error"
        
        url = "https://api.murf.ai/v1/speech/generate"
        headers = {
            "api-key": MURF_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "context_id": f"captain_blackbeard_{session_id}",
            "voiceId": voice_id,
            "format": "mp3",
            "sampleRate": 24000,
            "text": text,
            "encodedAudio": True
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                if resp.status != 200:
                    logger.error(f"[{session_id}] Murf API error: {resp.status}")
                    return False, None, "tts_error"
                
                data = await resp.json()
                audio_data = data.get("encodedAudio") or data.get("audioFile")
                
                if not audio_data:
                    return False, None, "tts_error"
                
                logger.info(f"[{session_id}] Generated pirate speech successfully")
                return True, audio_data, None
                
    except Exception as e:
        logger.error(f"[{session_id}] Speech generation error: {str(e)}")
        return False, None, "tts_error"


app = FastAPI(
    title="Captain Blackbeard's Voice Agent", 
    version="1.0.0",
    description="Ahoy! The most legendary AI pirate voice agent on the digital seas!"
)

SHIP_MEMORY = PirateMemoryStore()

BASE_DIR = PathLib(__file__).resolve().parent
UPLOADS_DIR = BASE_DIR / "uploads"
AUDIO_DIR = BASE_DIR / "audio_responses"
UPLOADS_DIR.mkdir(exist_ok=True)
AUDIO_DIR.mkdir(exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")
    

@app.get("/")
async def serve_frontend():
    """Serve the Captain Blackbeard frontend"""
    if os.path.exists("captain3.html"):
        return FileResponse("captain3.html")
    return JSONResponse({
        "message": "Ahoy! Captain Blackbeard's server be running!",
        "endpoints": {
            "health": "/health",
            "text_chat": "/chat/text",
            "voice_chat": "/chat/voice", 
            "audio_response": "/chat/audio-response",
            "history": "/chat/history/{session_id}"
        }
    })

@app.get("/health")
async def health_check():
    """Check if all ship systems are operational"""
    return {
        "status": "Sailing smoothly!",
        "captain": "Blackbeard",
        "ship_condition": "Seaworthy",
        "crew_status": SHIP_MEMORY.get_ship_stats(),
        "api_status": {
            "gemini_llm": bool(GEMINI_API_KEY),
            "assemblyai_stt": bool(ASSEMBLYAI_API_KEY),
            "murf_tts": bool(MURF_API_KEY)
        }
    }

@app.post("/process-audio")
async def process_audio(
    file: UploadFile = File(...),
    geminiKey: str = Form(...),
    assemblyKey: str = Form(None),
    murfKey: str = Form(...),
    weatherKey: str = Form(None),
    newsKey: str = Form(None)
):
    try:
        audio_bytes = await file.read()
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="wav")
        audio.export("temp.wav", format="wav")

        return JSONResponse({
            "message": "Audio processed!",
            "geminiKey": geminiKey,
            "assemblyKey": assemblyKey,
            "murfKey": murfKey,
            "weatherKey": weatherKey,
            "newsKey": newsKey
        })

    except Exception as e:
        print("Error processing audio:", e)
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/chat/text")
async def chat_with_captain(request: TextRequest):
    """Text chat with Captain Blackbeard"""
    session_id = request.session_id
    message = request.message.strip()
    
    if not message:
        return JSONResponse({
            "error": "Empty message, matey! Speak up!",
            "session_id": session_id
        }, status_code=400)
    
    try:
        SHIP_MEMORY.log_message(session_id, {
            "role": "user",
            "content": message,
            "timestamp": time.time()
        })
        conversation_prompt = build_pirate_conversation_prompt(session_id, message)
        success, response_text, error = await get_pirate_response(conversation_prompt, session_id)
        if not success:
            response_text = "Arrr! Something's amiss with me thinking cap! Try again, savvy?"
        
        SHIP_MEMORY.log_message(session_id, {
            "role": "assistant", 
            "content": response_text,
            "timestamp": time.time(),
            "error_type": error
        })
        
        recent_messages = SHIP_MEMORY.get_recent_voyage_log(session_id, 6)
        msg_models = []
        for m in recent_messages:
            msg_models.append(ChatMessage(
                role=m.get("role", "user"),
                content=m.get("content", ""),
                timestamp=m.get("timestamp", time.time()),
                error_type=m.get("error_type")
            ))
        
        return ChatResponse(
            session_id=session_id,
            response=response_text,
            message_count=len(SHIP_MEMORY.get_crew_messages(session_id)),
            recent_messages=msg_models,
            has_audio=False
        )
        
    except Exception as e:
        logger.error(f"[{session_id}] Chat error: {str(e)}")
        return JSONResponse({
            "error": "Shiver me timbers! Something went wrong in me quarters!",
            "session_id": session_id
        }, status_code=500)


@app.post("/config/keys")
async def update_keys(keys: Dict[str, str]):
    required = ["gemini", "assemblyai", "murf"]
    missing = [k for k in required if not keys.get(k)]
    if missing:
        return JSONResponse(
            {"error": f"Missing required keys: {', '.join(missing)}"},
            status_code=400
        )
    
    global GEMINI_API_KEY, ASSEMBLYAI_API_KEY, MURF_API_KEY, OPENWEATHER_API_KEY, NEWS_API_KEY

    GEMINI_API_KEY = keys.get("gemini", "")
    ASSEMBLYAI_API_KEY = keys.get("assemblyai", "")
    MURF_API_KEY = keys.get("murf", "")
    OPENWEATHER_API_KEY = keys.get("weather", "")
    NEWS_API_KEY = keys.get("news", "")

    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
    if ASSEMBLYAI_API_KEY:
        aai.settings.api_key = ASSEMBLYAI_API_KEY

    return {"status": "updated", "keys_set": [k for k, v in keys.items() if v]}


from fastapi import Query 
OPENWEATHER_API_KEY = ""

@app.get("/skill/weather")
async def get_weather(city: str = Query(...), session_id: str = Query(None)):
    """Fetch current weather for a city, with pirate flair ⚓"""
    if not OPENWEATHER_API_KEY:
        return {"error": "Arrr! No weather API key be configured in me treasure chest."}

    try:
        clean_city = city.strip("?.!,; ")
        url = f"http://api.openweathermap.org/data/2.5/weather?q={clean_city}&appid={OPENWEATHER_API_KEY}&units=metric"
        r = requests.get(url, timeout=5)

        if r.status_code != 200:
            return {"error": f"Blimey! Could not fetch the skies over {clean_city}, matey."}

        data = r.json()
        desc = data["weather"][0]["description"]
        temp = data["main"]["temp"]

        pirate_msg = (
            f"🌦️ Ahoy! In {clean_city}, the weather be {desc}, "
            f"with the seas at {temp}°C. Batten down the hatches if needed, arrr!"
        )

        if session_id:
            SHIP_MEMORY.log_message(session_id, {
                "role": "assistant",
                "content": pirate_msg,
                "timestamp": time.time(),
                "error_type": None
            })

        return {
            "city": clean_city,
            "weather": desc,
            "temperature": f"{temp} °C",
            "pirate_report": pirate_msg
        }
    except Exception as e:
        return {"error": f"Shiver me timbers! The weather service failed: {str(e)}"}

NEWS_API_KEY = ""
@app.get("/skill/news")
async def get_news(topic: str = "technology", session_id: str = Query(None)):
    """Fetch top headlines or articles for a given topic"""
    if not NEWS_API_KEY:
        return {"error": "Arrr! No news API key be configured, matey."}
    try:
        url = f"https://newsapi.org/v2/everything?q={topic}&sortBy=publishedAt&apiKey={NEWS_API_KEY}&language=en&pageSize=3"
        r = requests.get(url, timeout=5)
        if r.status_code != 200:
            return {"error": f"Blimey! Could not fetch news on {topic}, matey."}

        data = r.json()
        articles = data.get("articles", [])
        if not articles:
            return {"message": f"Arrr! No fresh tales on {topic}, me hearty."}

        headlines = [a.get("title", "Mystery tale with no title") for a in articles[:3]]
        pirate_news = "Hear ye, matey! Fresh tales :\n- " + "\n- ".join(headlines)
        if session_id:
            SHIP_MEMORY.log_message(session_id, {
                "role": "assistant",
                "content": pirate_news,
                "timestamp": time.time(),
                "error_type": None
        })
        return {"news": pirate_news}

    except Exception as e:
        return {"error": f"Shiver me timbers! News service failed: {str(e)}"}

@app.get("/skill/shanty")
async def generate_sea_shanty():
    """Generate a short pirate sea shanty"""
    shanties = [
        "🎵 Yo ho ho, we code till night, chasing bugs by lantern light! 🎵",
        "🎵 Shiver me timbers, the AI be grand, guiding our ship with a coder’s hand! 🎵",
        "🎵 Heave ho matey, let’s set sail, with datasets vast and models that scale! 🎵",
        "🎵 Hoist the sails and man the oars, our code be smoother than ocean shores! 🎵",
        "🎵 Arrr, no storm can bring us down, we debug with a coder’s crown! 🎵"
    ]
    return {"shanty": random.choice(shanties)}

@app.post("/chat/voice")
async def voice_chat_with_captain(
    session_id: str = Form(...),
    audio: UploadFile = File(...)
):
    """Voice chat with Captain Blackbeard"""
    
    if not audio.content_type or not (
        audio.content_type.startswith("audio/") or audio.content_type.startswith("video/")
    ):
        return JSONResponse({
             "error": "That don't sound like proper audio, matey!",
             "session_id": session_id
        }, status_code=400)

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            content = await audio.read()
            if len(content) == 0:
                return JSONResponse({
                    "error": "Empty bottle! No message heard!",
                    "session_id": session_id
                }, status_code=400)
            tmp.write(content)
            tmp_path = tmp.name
        
        stt_success, transcribed_text, stt_error = await transcribe_speech(tmp_path, session_id)
        
        if not stt_success:
            return JSONResponse({
                "error": transcribed_text,
                "session_id": session_id,
                "transcription_error": stt_error
            }, status_code=400)
        
        SHIP_MEMORY.log_message(session_id, {
            "role": "user",
            "content": transcribed_text,
            "timestamp": time.time()
        })
        
        lower = transcribed_text.lower()
        response_text = ""
        has_audio = False
        audio_data = None
        llm_error = None
        tts_error = None

        if "weather" in lower:
            import re
            match = re.search(r"weather (in|at|of)?\s*(.*)", lower)
            city = match.group(2).strip() if match and match.group(2) else "the high seas"
            result = await get_weather(city=city, session_id=session_id)
            response_text = result.get("pirate_report") or result.get("error", "Arrr! No forecast today, matey!")
        
        elif "news" in lower:
            topic = lower.split("news")[-1].strip() or "technology"
            result = await get_news(topic=topic, session_id=session_id)
            response_text = result.get("news") or result.get("message") or result.get("error", "Blimey! Could not fetch news, matey.")

        elif "shanty" in lower:
            result = await generate_sea_shanty()
            response_text = result.get("shanty") or "Arrr! Me voice be too hoarse for singin’, matey!"

        if not response_text:
            conversation_prompt = build_pirate_conversation_prompt(session_id, transcribed_text)
            llm_success, response_text, llm_error = await get_pirate_response(conversation_prompt, session_id)
            if not llm_success:
                response_text = "Blast! Me thinking be all muddled! What was that again?"
        
        SHIP_MEMORY.log_message(session_id, {
            "role": "assistant",
            "content": response_text, 
            "timestamp": time.time(),
            "error_type": llm_error
        })
        
        tts_success, audio_data, tts_error = await generate_pirate_speech(response_text, "en-US-marcus", session_id)
        has_audio = tts_success
        
        recent_messages = SHIP_MEMORY.get_recent_voyage_log(session_id, 6)
        msg_models = []
        for m in recent_messages:
            msg_models.append(ChatMessage(
                role=m.get("role", "user"),
                content=m.get("content", ""),
                timestamp=m.get("timestamp", time.time()),
                error_type=m.get("error_type")
            ))
        
        return {
            "session_id": session_id,
            "transcribed_text": transcribed_text,
            "response": response_text,
            "message_count": len(SHIP_MEMORY.get_crew_messages(session_id)),
            "recent_messages": [m.dict() for m in msg_models],
            "has_audio": has_audio,
            "audio_data": audio_data if has_audio else None,
            "errors": {
                "stt_error": stt_error,
                "llm_error": llm_error, 
                "tts_error": tts_error
            }
        }
        
    except Exception as e:
        logger.error(f"[{session_id}] Voice chat error: {str(e)}")
        return JSONResponse({
            "error": "Arrr! The seas be too rough for voice messages right now!",
            "session_id": session_id
        }, status_code=500)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except:
                pass

@app.post("/chat/audio-response")
async def generate_audio_response(request: AudioRequest):
    """Generate audio response from text"""
    try:
        success, audio_data, error = await generate_pirate_speech(
            request.text, 
            request.voice_id,
            "audio_generation"
        )
        
        if success and audio_data:
            
            if audio_data.startswith("data:audio") or len(audio_data) > 1000:
                audio_bytes = base64.b64decode(audio_data)
                return StreamingResponse(
                    io.BytesIO(audio_bytes),
                    media_type="audio/mp3",
                    headers={"Content-Disposition": "attachment; filename=pirate_response.mp3"}
                )
            else:
                return JSONResponse({"audio_url": audio_data})
        else:
            return JSONResponse({
                "error": "Couldn't generate me voice, but here's the message!",
                "text": request.text
            }, status_code=500)
            
    except Exception as e:
        logger.error(f"Audio response error: {str(e)}")
        return JSONResponse({
            "error": "Voice generation failed, matey!",
            "text": request.text
        }, status_code=500)

@app.get("/chat/history/{session_id}")
async def get_voyage_history(session_id: str):
    """Get chat history for a session"""
    messages = SHIP_MEMORY.get_crew_messages(session_id)
    return {
        "session_id": session_id,
        "message_count": len(messages),
        "messages": messages,
        "ship_stats": SHIP_MEMORY.get_ship_stats()
    }

@app.delete("/chat/history/{session_id}")
async def clear_voyage_history(session_id: str):
    """Clear chat history for a session"""
    SHIP_MEMORY.clear_crew_records(session_id)
    return {
        "success": True,
        "message": f"Cleared all records for crew member {session_id}, savvy!"
    }

@app.get("/ship/stats")
async def get_ship_statistics():
    """Get overall ship and crew statistics"""
    return {
        "captain": "Blackbeard",
        "ship_status": "Sailing the digital seas",
        "stats": SHIP_MEMORY.get_ship_stats(),
        "api_status": {
            "gemini_llm": "⚓" if GEMINI_API_KEY else "❌",
            "assemblyai_stt": "⚓" if ASSEMBLYAI_API_KEY else "❌", 
            "murf_tts": "⚓" if MURF_API_KEY else "❌"
        }
    }

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse({
        "error": "Arrr! That treasure map leads to nowhere, matey!",
        "message": "Endpoint not found on this vessel"
    }, status_code=404)

@app.exception_handler(500) 
async def internal_error_handler(request, exc):
    return JSONResponse({
        "error": "Shiver me timbers! Something went wrong in the engine room!",
        "message": "Internal server error"
    }, status_code=500)

if __name__ == "__main__":
    import uvicorn
    import io
    
    print(" AHOY! Starting Captain Blackbeard's Voice Agent Server...")
    print("  The most legendary AI pirate on the digital seas!")
    print()
    print("    Server will be sailing at: http://127.0.0.1:5000")
    print("    Health check: http://127.0.0.1:5000/health")
    print("    Ship stats: http://127.0.0.1:5000/ship/stats")
    print()
    print("    Features aboard this vessel:")
    print("    Voice transcription (Speech-to-Text)")
    print("    Pirate persona with Gemini LLM")
    print("    Voice synthesis (Text-to-Speech)")
    print("    Conversation memory management")
    print("    Text and voice chat endpoints")
    print("    Full pirate personality and vocabulary")
    print("    Error handling with pirate flair")
    print()
    print("   Ready to help ye navigate the digital seas, matey! Arrr!")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5000,
        log_level="info"
    )
