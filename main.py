import os
import tempfile
import logging
import uuid
import time
from typing import Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, Form, HTTPException, File
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydub import AudioSegment

from schemas.models import (
    ErrorType,
    ChatMessage as ChatMessageModel,
    ChatResponse,
    ErrorResponse,
    HistoryResponse,
)
from services.memory import MemoryStore
from services.stt import speech_to_text
from services.llm import generate_response
from services.tts import text_to_speech

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path, override=True)

# ===== CONFIGURATION =====
def safe_env_get(key: str, required: bool = False, default: str = "") -> str:
    """Safely get environment variable with error handling"""
    value = os.getenv(key, default)
    if required and (not value or value.strip() == "" or value.strip() == "your_api_key_here"):
        logging.getLogger("voice_agent").warning(f"⚠️  Required environment variable {key} is missing or invalid")
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
ASSEMBLYAI_API_KEY = safe_env_get("ASSEMBLYAI_API_KEY", required=True) 
GEMINI_API_KEY = safe_env_get("GEMINI_API_KEY", required=True)  
MURF_API_KEY = safe_env_get("MURF_API_KEY", required=True)  

GTTS_AVAILABLE = safe_env_get("USE_GTTS_FALLBACK", default="true").Lowerin()=="true"


# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("voice_agent")


# FastAPI app
app = FastAPI(title="Robust AI Voice Agent", version="2.1.0")

# Mount static directory for CSS/JS
if os.path.isdir("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Persistent conversation memory
MEMORY = MemoryStore(base_dir="data/sessions")

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
def log_error(error_type: ErrorType, session_id: str, details: str):
    """Log and track errors"""
    ERROR_COUNTS[error_type] += 1
    logger.error(f"[{session_id}] {error_type.value}: {details}")

def create_error_response(error_type: ErrorType, session_id: str, details: str = ""):
    """Create standardized error response"""
    log_error(error_type, session_id, details)
    fallback_text = FALLBACK_RESPONSES[error_type]
    # Defer to services.tts for fallback behavior at client side via TEXT_ONLY
    fallback_audio = f"TEXT_ONLY:{fallback_text}"
    
    return ErrorResponse(
        error_type=error_type,
        session_id=session_id,
        llm_response=fallback_text,
        audioFile=fallback_audio,
        error_details=details,
    ).model_dump()

# ===== CORE FUNCTIONS WITH ERROR HANDLING =====
async def robust_speech_to_text(file_path: str, session_id: str) -> tuple[bool, str, Optional[ErrorType]]:
    return await speech_to_text(file_path=file_path, session_id=session_id, logger=logger, api_configured=bool(ASSEMBLYAI_API_KEY))

def robust_llm_response(prompt: str, session_id: str) -> tuple[bool, str, Optional[ErrorType]]:
    return generate_response(prompt=prompt, session_id=session_id, logger=logger, api_configured=bool(GEMINI_API_KEY))

async def robust_text_to_speech(text: str, voice_id: str, session_id: str) -> tuple[bool, str, Optional[ErrorType]]:
    return await text_to_speech(text=text, voice_id=voice_id, session_id=session_id, logger=logger, murf_configured=bool(MURF_API_KEY))

def build_conversation_prompt(session_id: str, new_user_message: str) -> str:
    """Build conversation prompt including chat history"""
    history = MEMORY.get_messages(session_id)
    summary = MEMORY.get_summary(session_id)
    
    system_prompt = (
        "You are a helpful, friendly AI voice assistant. "
        "Respond naturally and conversationally with clear, concise answers "
        "suitable for text-to-speech conversion. Keep responses under 200 words "
        "unless specifically asked for detailed information. "
        "If you detect any errors or issues, provide helpful guidance.\n\n"
    )
    
    prompt_parts = [system_prompt]
    if summary:
        prompt_parts.append(f"Conversation summary so far: {summary}\n")
    
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
    
    # Ensure memory file initialized lazily
    
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

        # Step 2: Add user message to memory
        MEMORY.append_message(session_id, {
            "role": "user",
            "content": transcription_text,
            "timestamp": time.time(),
            "error_type": None,
        })

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

        # Step 5: Add assistant response to memory
        MEMORY.append_message(session_id, {
            "role": "assistant",
            "content": llm_response_text,
            "timestamp": time.time(),
            "error_type": llm_error.value if llm_error else None,
        })

        # Step 5.1: Periodically update session summary to keep context tight
        total = len(MEMORY.get_messages(session_id))
        if total % 10 == 0:
            # Simple extractive summary heuristic: keep last user + assistant, and a lightweight header
            recent = MEMORY.get_recent_messages(session_id, limit=10)
            key_points = []
            for m in recent:
                role = m.get("role")
                content = (m.get("content") or "").strip()
                if not content:
                    continue
                if role == "user":
                    key_points.append(f"User asked: {content[:180]}")
                elif role == "assistant":
                    key_points.append(f"Assistant answered: {content[:180]}")
            new_summary = " | ".join(key_points[-6:])
            try:
                MEMORY.set_summary(session_id, new_summary)
            except Exception:
                pass

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

        # Step 8: Return complete response (schema)
        recent_messages = MEMORY.get_recent_messages(session_id, limit=6)
        msg_models: List[ChatMessageModel] = [
            ChatMessageModel(**{
                "role": m.get("role", "user"),
                "content": m.get("content", ""),
                "timestamp": m.get("timestamp", time.time()),
                "error_type": m.get("error_type"),
            }) for m in recent_messages
        ]
        resp = ChatResponse(
            session_id=session_id,
            transcription=transcription_text,
            llm_response=llm_response_text,
            audioFile=audio_url,
            voice_id=voice_id,
            message_count=len(MEMORY.get_messages(session_id)),
            recent_messages=msg_models,
            pipeline_status={
                    "stt_success": stt_success,
                    "llm_success": llm_success,
                    "tts_success": tts_success,
                "errors": [e.value for e in [stt_error, llm_error, tts_error] if e],
            },
        )
        return JSONResponse(content=resp.model_dump())

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
    messages = MEMORY.get_messages(session_id)
    error_summary = MEMORY.error_summary(session_id)
    return JSONResponse(content={
            "session_id": session_id,
            "message_count": len(messages),
            "messages": messages,
        "error_summary": error_summary,
    })

@app.delete("/agent/chat/{session_id}/history")
def clear_chat_history(session_id: str):
    """Clear chat history for a session"""
    MEMORY.clear_session(session_id)
    return JSONResponse(content={
                "success": True,
        "message": f"Chat history cleared for session {session_id}",
    })

@app.get("/agent/diagnostics")
def get_diagnostics():
    """Get system diagnostics and error statistics"""
    stats = MEMORY.stats()
    return JSONResponse(content={
            "system_status": {
            "total_sessions": len(stats),
            "total_messages": MEMORY.total_messages(),
                "api_keys_configured": {
                    "assemblyai": bool(ASSEMBLYAI_API_KEY),
                    "gemini": bool(GEMINI_API_KEY),
                "murf": bool(MURF_API_KEY),
            },
            "fallback_available": True,
            },
            "error_statistics": {k.value: v for k, v in ERROR_COUNTS.items()},
        "active_sessions": list(stats.values()),
    })

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
    print(" API Status:")
    print(f"   - AssemblyAI: {'✅' if ASSEMBLYAI_API_KEY else '❌'}")
    print(f"   - Gemini: {'✅' if GEMINI_API_KEY else '❌'}")
    print(f"   - Murf: {'✅' if MURF_API_KEY else '❌'}")
    print(f"   - gTTS Fallback: ✅")
    print("🌐 Server will be available at: http://127.0.0.1:8000")
    print("🩺 Diagnostics available at: http://127.0.0.1:8000/agent/diagnostics")
    
    uvicorn.run(
        app, 
        host="127.0.0.1", 
        port=8000, 
        workers=1
    )