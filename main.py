import os
import sys
import tempfile
import logging
import shutil
import uuid
import json
import time
import base64
import io
from typing import Dict, List, TypedDict, Optional
from enum import Enum

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, Form, HTTPException, File
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydub import AudioSegment
import httpx
import requests
import assemblyai as aai
import google.generativeai as genai

# Error handling for fallback TTS
try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path, override=True)

# ===== ERROR CATEGORIES =====
class ErrorType(Enum):
    STT_ERROR = "stt_error"
    LLM_ERROR = "llm_error"
    TTS_ERROR = "tts_error"
    FILE_ERROR = "file_error"
    NETWORK_ERROR = "network_error"
    CONFIG_ERROR = "config_error"

# ===== CONFIGURATION =====
def safe_env_get(key: str, required: bool = False, default: str = "") -> str:
    """Safely get environment variable with error handling"""
    value = os.getenv(key, default)
    if required and (not value or value.strip() == "" or value.strip() == "your_api_key_here"):
        logger.warning(f"⚠️  Required environment variable {key} is missing or invalid")
        return ""
    return value

# Configure FFmpeg paths
ffmpeg_path = safe_env_get("FFMPEG_PATH")
if ffmpeg_path and os.path.exists(ffmpeg_path):
    try:
        AudioSegment.converter = os.path.join(ffmpeg_path, "ffmpeg.exe") if os.name == "nt" else os.path.join(ffmpeg_path, "ffmpeg")
        AudioSegment.ffprobe = os.path.join(ffmpeg_path, "ffprobe.exe") if os.name == "nt" else os.path.join(ffmpeg_path, "ffprobe")
    except Exception as e:
        logging.warning(f"FFmpeg configuration failed: {e}")

# API Keys with error handling
ASSEMBLYAI_API_KEY = safe_env_get("ASSEMBLYAI_API_KEY", required=True)  # SIMULATED FAILURE  # SIMULATED FAILURE
GEMINI_API_KEY = safe_env_get("GEMINI_API_KEY", required=True)  # SIMULATED FAILURE  # SIMULATED FAILURE  # SIMULATED FAILURE
MURF_API_KEY = safe_env_get("MURF_API_KEY", required=True)  # SIMULATED FAILURE  # SIMULATED FAILURE

# Configure APIs with error handling
try:
    if ASSEMBLYAI_API_KEY:
        aai.settings.api_key = ASSEMBLYAI_API_KEY
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    logging.error(f"API configuration failed: {e}")

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("voice_agent")

# FastAPI app
app = FastAPI(title="Robust AI Voice Agent", version="2.0.0")

# Chat History Data Structure
class ChatMessage(TypedDict):
    role: str  # "user" | "assistant" | "system"
    content: str
    timestamp: float
    error_type: Optional[str]

CHAT_HISTORY: Dict[str, List[ChatMessage]] = {}

# Error tracking
ERROR_COUNTS = {
    ErrorType.STT_ERROR: 0,
    ErrorType.LLM_ERROR: 0,
    ErrorType.TTS_ERROR: 0,
    ErrorType.FILE_ERROR: 0,
    ErrorType.NETWORK_ERROR: 0,
    ErrorType.CONFIG_ERROR: 0,
}

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== FALLBACK RESPONSES =====
FALLBACK_RESPONSES = {
    ErrorType.STT_ERROR: "I'm sorry, I'm having trouble understanding your audio right now. Could you please try speaking again?",
    ErrorType.LLM_ERROR: "I'm experiencing some technical difficulties processing your request. Please try again in a moment.",
    ErrorType.TTS_ERROR: "I understood your request but I'm having trouble generating audio. Here's my text response.",
    ErrorType.FILE_ERROR: "There seems to be an issue with your audio file. Please try recording again.",
    ErrorType.NETWORK_ERROR: "I'm having trouble connecting to my services right now. Please check your connection and try again.",
    ErrorType.CONFIG_ERROR: "The service is temporarily unavailable due to configuration issues. Please try again later.",
}

# ===== UTILITY FUNCTIONS =====
def generate_fallback_audio(text: str) -> str:
    """Generate simple fallback audio using basic TTS or return text"""
    if not GTTS_AVAILABLE:
        logger.warning("gTTS not available, returning text response")
        return f"TEXT_ONLY:{text}"
    
    try:
        tts = gTTS(text=text, lang="en", slow=False)
        buffer = io.BytesIO()
        tts.write_to_fp(buffer)
        buffer.seek(0)
        b64 = base64.b64encode(buffer.read()).decode("utf-8")
        return f"data:audio/mp3;base64,{b64}"
    except Exception as e:
        logger.error(f"Fallback TTS failed: {e}")
        return f"TEXT_ONLY:{text}"

def log_error(error_type: ErrorType, session_id: str, details: str):
    """Log and track errors"""
    ERROR_COUNTS[error_type] += 1
    logger.error(f"[{session_id}] {error_type.value}: {details}")

def create_error_response(error_type: ErrorType, session_id: str, details: str = ""):
    """Create standardized error response"""
    log_error(error_type, session_id, details)
    fallback_text = FALLBACK_RESPONSES[error_type]
    fallback_audio = generate_fallback_audio(fallback_text)
    
    return {
        "success": False,
        "error_type": error_type.value,
        "session_id": session_id,
        "transcription": "",
        "llm_response": fallback_text,
        "audioFile": fallback_audio,
        "error_details": details,
        "fallback_used": True,
        "retry_suggested": True
    }

# ===== CORE FUNCTIONS WITH ERROR HANDLING =====
async def robust_speech_to_text(file_path: str, session_id: str) -> tuple[bool, str, Optional[ErrorType]]:
    """Robust speech-to-text with error handling and fallbacks"""
    if not ASSEMBLYAI_API_KEY:
        return False, "", ErrorType.CONFIG_ERROR
    
    try:
        # Validate file exists and is readable
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            return False, "", ErrorType.FILE_ERROR
        
        config = aai.TranscriptionConfig(
            speaker_labels=False,
            punctuate=True,
            format_text=True,
            language_code="en",
        )
        
        transcriber = aai.Transcriber(config=config)
        transcript = transcriber.transcribe(file_path)
        
        if transcript.status == aai.TranscriptStatus.error:
            logger.error(f"AssemblyAI transcription error: {transcript.error}")
            return False, "", ErrorType.STT_ERROR
        
        transcription_text = transcript.text or ""
        if not transcription_text.strip():
            return False, "", ErrorType.STT_ERROR
        
        logger.info(f"[{session_id}] STT Success: {len(transcription_text)} characters")
        return True, transcription_text, None
        
    except requests.exceptions.RequestException as e:
        logger.error(f"[{session_id}] STT Network error: {e}")
        return False, "", ErrorType.NETWORK_ERROR
    except Exception as e:
        logger.error(f"[{session_id}] STT Unexpected error: {e}")
        return False, "", ErrorType.STT_ERROR

def robust_llm_response(prompt: str, session_id: str) -> tuple[bool, str, Optional[ErrorType]]:
    """Robust LLM response with error handling and fallbacks"""
    if not GEMINI_API_KEY:
        return False, "", ErrorType.CONFIG_ERROR
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        
        if not response or not response.text:
            return False, "", ErrorType.LLM_ERROR
        
        result = response.text.strip()
        logger.info(f"[{session_id}] LLM Success: {len(result)} characters")
        return True, result, None
        
    except genai.types.BlockedPromptException as e:
        logger.error(f"[{session_id}] LLM Blocked prompt: {e}")
        fallback = "I'm sorry, I can't respond to that type of request. Could you please ask something else?"
        return True, fallback, None
    except requests.exceptions.RequestException as e:
        logger.error(f"[{session_id}] LLM Network error: {e}")
        return False, "", ErrorType.NETWORK_ERROR
    except Exception as e:
        logger.error(f"[{session_id}] LLM Unexpected error: {e}")
        return False, "", ErrorType.LLM_ERROR

async def robust_text_to_speech(text: str, voice_id: str, session_id: str) -> tuple[bool, str, Optional[ErrorType]]:
    """Robust TTS with multiple fallback strategies"""
    if not MURF_API_KEY:
        logger.warning(f"[{session_id}] No Murf API key, using fallback TTS")
        fallback_audio = generate_fallback_audio(text)
        return True, fallback_audio, None
    
    # Trim long text for TTS safety
    if len(text) > 3000:
        text = text[:2950] + "..."
    
    murf_api_url = "https://api.murf.ai/v1/speech/generate"
    
    async def attempt_murf_request(headers: dict, payload: dict) -> tuple[bool, str | dict]:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(murf_api_url, headers=headers, json=payload)
                if resp.status_code == 200:
                    return True, resp.json()
                else:
                    logger.warning(f"[{session_id}] Murf API returned {resp.status_code}")
                    return False, f"HTTP {resp.status_code}"
        except httpx.TimeoutException:
            logger.error(f"[{session_id}] Murf API timeout")
            return False, "Timeout"
        except Exception as e:
            logger.error(f"[{session_id}] Murf API error: {e}")
            return False, str(e)
    
    # Try Murf API with different configurations
    payload_variants = [
        {
            "text": text,
            "voiceId": voice_id,
            "format": "mp3",
            "speed": 1.0,
            "pitch": 1.0,
            "volume": 1.0,
            "pauseAfter": 0,
            "encodeAsBase64": False,
        },
        {
            "text": text,
            "voice": voice_id,
            "format": "mp3",
            "speed": 1.0,
            "pitch": 1.0,
            "volume": 1.0,
            "pauseAfter": 0,
            "encodeAsBase64": False,
        }
    ]
    
    header_variants = [
        {
            "Authorization": f"Bearer {MURF_API_KEY}",
            "Content-Type": "application/json",
        },
        {
            "api-key": MURF_API_KEY,
            "Content-Type": "application/json",
        }
    ]
    
    # Try different combinations
    for headers in header_variants:
        for payload in payload_variants:
            success, data = await attempt_murf_request(headers, payload)
            if success:
                result = data
                # Look for audio URL in response
                audio_url = (
                    result.get("audioFile") or 
                    result.get("url") or 
                    result.get("audioUrl")
                )
                if audio_url:
                    logger.info(f"[{session_id}] Murf TTS Success")
                    return True, audio_url, None
                
                # Look for base64 audio data
                audio_data = result.get("audioData") or result.get("audioBase64")
                if audio_data:
                    logger.info(f"[{session_id}] Murf TTS Success (base64)")
                    return True, f"data:audio/mp3;base64,{audio_data}", None
    
    # Fallback to gTTS
    logger.warning(f"[{session_id}] Murf API failed, falling back to gTTS")
    fallback_audio = generate_fallback_audio(text)
    return True, fallback_audio, None

def build_conversation_prompt(session_id: str, new_user_message: str) -> str:
    """Build conversation prompt including chat history"""
    history = CHAT_HISTORY.get(session_id, [])
    
    system_prompt = (
        "You are a helpful, friendly AI voice assistant. "
        "Respond naturally and conversationally with clear, concise answers "
        "suitable for text-to-speech conversion. Keep responses under 200 words "
        "unless specifically asked for detailed information. "
        "If you detect any errors or issues, provide helpful guidance.\n\n"
    )
    
    prompt_parts = [system_prompt]
    
    # Include recent history (last 10 exchanges to manage token limits)
    recent_history = history[-20:] if len(history) > 20 else history
    
    for msg in recent_history:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if content and not msg.get("error_type"):  # Skip error messages from history
            if role == "user":
                prompt_parts.append(f"Human: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
    
    # Add new user message
    prompt_parts.append(f"Human: {new_user_message}")
    prompt_parts.append("Assistant:")
    
    return "\n".join(prompt_parts)

# ===== API ENDPOINTS =====
@app.get("/")
async def read_index():
    return FileResponse("templates/index.html")

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "Robust AI Voice Agent server is running",
        "api_status": {
            "assemblyai": bool(ASSEMBLYAI_API_KEY),
            "gemini": bool(GEMINI_API_KEY),
            "murf": bool(MURF_API_KEY),
            "gtts_fallback": GTTS_AVAILABLE
        },
        "error_counts": {k.value: v for k, v in ERROR_COUNTS.items()}
    }

@app.post("/agent/chat/{session_id}")
async def agent_chat_with_history(
    session_id: str,
    file: UploadFile = File(...),
    voice_id: str = Form(default="en-US-natalie"),
):
    """
    Robust conversational AI pipeline with comprehensive error handling:
    Audio Input -> Speech-to-Text -> Add to Chat History -> LLM -> 
    Update Chat History -> Text-to-Speech -> Audio Output
    """
    
    # Initialize session if needed
    if session_id not in CHAT_HISTORY:
        CHAT_HISTORY[session_id] = []
    
    # Validate audio file
    content_type = file.content_type or ""
    if not content_type.startswith("audio/") and content_type != "application/octet-stream":
        return JSONResponse(
            content=create_error_response(
                ErrorType.FILE_ERROR, 
                session_id, 
                f"Invalid file type: {content_type}"
            ),
            status_code=400
        )

    tmp_path = None
    try:
        # Save uploaded audio to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            content = await file.read()
            if len(content) == 0:
                return JSONResponse(
                    content=create_error_response(
                        ErrorType.FILE_ERROR, 
                        session_id, 
                        "Empty audio file received"
                    ),
                    status_code=400
                )
            tmp.write(content)
            tmp_path = tmp.name

        # Step 1: Robust Speech-to-Text
        logger.info(f"[{session_id}] Starting STT pipeline")
        stt_success, transcription_text, stt_error = await robust_speech_to_text(tmp_path, session_id)
        
        if not stt_success:
            return JSONResponse(
                content=create_error_response(
                    stt_error or ErrorType.STT_ERROR, 
                    session_id, 
                    "Speech transcription failed"
                ),
                status_code=500
            )

        # Step 2: Add user message to chat history
        user_message = {
            "role": "user",
            "content": transcription_text,
            "timestamp": time.time(),
            "error_type": None
        }
        CHAT_HISTORY[session_id].append(user_message)

        # Step 3: Build prompt with conversation context
        conversation_prompt = build_conversation_prompt(session_id, transcription_text)
        
        # Step 4: Robust LLM Response
        logger.info(f"[{session_id}] Starting LLM pipeline")
        llm_success, llm_response_text, llm_error = robust_llm_response(conversation_prompt, session_id)
        
        if not llm_success:
            error_response = create_error_response(
                llm_error or ErrorType.LLM_ERROR, 
                session_id, 
                "LLM response generation failed"
            )
            llm_response_text = error_response["llm_response"]

        # Step 5: Add assistant response to chat history
        assistant_message = {
            "role": "assistant",
            "content": llm_response_text,
            "timestamp": time.time(),
            "error_type": llm_error.value if llm_error else None
        }
        CHAT_HISTORY[session_id].append(assistant_message)

        # Step 6: Limit chat history size
        if len(CHAT_HISTORY[session_id]) > 100:
            CHAT_HISTORY[session_id] = CHAT_HISTORY[session_id][-80:]

        # Step 7: Robust Text-to-Speech
        logger.info(f"[{session_id}] Starting TTS pipeline")
        tts_success, audio_url, tts_error = await robust_text_to_speech(llm_response_text, voice_id, session_id)
        
        if not tts_success:
            error_response = create_error_response(
                tts_error or ErrorType.TTS_ERROR, 
                session_id, 
                "Text-to-speech generation failed"
            )
            audio_url = error_response["audioFile"]

        # Step 8: Return complete response
        return JSONResponse(
            content={
                "success": True,
                "session_id": session_id,
                "transcription": transcription_text,
                "llm_response": llm_response_text,
                "audioFile": audio_url,
                "voice_id": voice_id,
                "message_count": len(CHAT_HISTORY[session_id]),
                "recent_messages": CHAT_HISTORY[session_id][-6:],
                "pipeline_status": {
                    "stt_success": stt_success,
                    "llm_success": llm_success,
                    "tts_success": tts_success,
                    "errors": [e.value for e in [stt_error, llm_error, tts_error] if e]
                }
            }
        )

    except Exception as e:
        logger.error(f"[{session_id}] Unexpected pipeline error: {e}")
        return JSONResponse(
            content=create_error_response(
                ErrorType.NETWORK_ERROR, 
                session_id, 
                f"Unexpected error: {str(e)}"
            ),
            status_code=500
        )
    finally:
        # Cleanup temp file
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup temp file: {cleanup_error}")

# ===== ADDITIONAL ENDPOINTS =====
@app.get("/agent/chat/{session_id}/history")
def get_chat_history(session_id: str):
    """Retrieve chat history for a session"""
    messages = CHAT_HISTORY.get(session_id, [])
    return JSONResponse(
        content={
            "session_id": session_id,
            "message_count": len(messages),
            "messages": messages,
            "error_summary": {
                error_type.value: len([m for m in messages if m.get("error_type") == error_type.value])
                for error_type in ErrorType
            }
        }
    )

@app.delete("/agent/chat/{session_id}/history")
def clear_chat_history(session_id: str):
    """Clear chat history for a session"""
    if session_id in CHAT_HISTORY:
        del CHAT_HISTORY[session_id]
        return JSONResponse(
            content={
                "success": True,
                "message": f"Chat history cleared for session {session_id}"
            }
        )
    else:
        return JSONResponse(
            content={
                "success": False,
                "message": f"No chat history found for session {session_id}"
            },
            status_code=404
        )

@app.get("/agent/diagnostics")
def get_diagnostics():
    """Get system diagnostics and error statistics"""
    return JSONResponse(
        content={
            "system_status": {
                "total_sessions": len(CHAT_HISTORY),
                "total_messages": sum(len(msgs) for msgs in CHAT_HISTORY.values()),
                "api_keys_configured": {
                    "assemblyai": bool(ASSEMBLYAI_API_KEY),
                    "gemini": bool(GEMINI_API_KEY),
                    "murf": bool(MURF_API_KEY)
                },
                "fallback_available": GTTS_AVAILABLE
            },
            "error_statistics": {k.value: v for k, v in ERROR_COUNTS.items()},
            "active_sessions": [
                {
                    "session_id": sid, 
                    "message_count": len(msgs),
                    "last_activity": max(msg.get("timestamp", 0) for msg in msgs) if msgs else 0,
                    "error_count": len([m for m in msgs if m.get("error_type")])
                }
                for sid, msgs in CHAT_HISTORY.items()
            ]
        }
    )

@app.post("/test/simulate-error/{error_type}")
async def simulate_error(error_type: str):
    """Endpoint to simulate different error scenarios for testing"""
    if error_type not in [e.value for e in ErrorType]:
        raise HTTPException(status_code=400, detail="Invalid error type")
    
    test_session = f"test_{uuid.uuid4().hex[:8]}"
    error_enum = ErrorType(error_type)
    
    response = create_error_response(error_enum, test_session, "Simulated error for testing")
    
    return JSONResponse(content=response)

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Robust AI Voice Agent Server...")
    print(" Enhanced with comprehensive error handling and fallbacks")
    print("🔧 API Status:")
    print(f"   - AssemblyAI: {'✅' if ASSEMBLYAI_API_KEY else '❌'}")
    print(f"   - Gemini: {'✅' if GEMINI_API_KEY else '❌'}")
    print(f"   - Murf: {'✅' if MURF_API_KEY else '❌'}")
    print(f"   - gTTS Fallback: {'✅' if GTTS_AVAILABLE else '❌'}")
    print("🌐 Server will be available at: http://127.0.0.1:8000")
    print("🩺 Diagnostics available at: http://127.0.0.1:8000/agent/diagnostics")
    
    uvicorn.run(
        app, 
        host="127.0.0.1", 
        port=8000, 
        workers=1
    )