from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ErrorType(str, Enum):
    STT_ERROR = "stt_error"
    LLM_ERROR = "llm_error"
    TTS_ERROR = "tts_error"
    FILE_ERROR = "file_error"
    NETWORK_ERROR = "network_error"
    CONFIG_ERROR = "config_error"


class ChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant|system)$")
    content: str
    timestamp: float
    error_type: Optional[str] = None


class PipelineStatus(BaseModel):
    stt_success: bool
    llm_success: bool
    tts_success: bool
    errors: List[str] = []


class ChatResponse(BaseModel):
    success: bool = True
    session_id: str
    transcription: str
    llm_response: str
    audioFile: Optional[str] = None
    voice_id: Optional[str] = None
    message_count: int
    recent_messages: List[ChatMessage] = []
    pipeline_status: PipelineStatus
    fallback_used: Optional[bool] = False


class ErrorResponse(BaseModel):
    success: bool = False
    error_type: ErrorType
    session_id: str
    transcription: str = ""
    llm_response: str
    audioFile: Optional[str] = None
    error_details: Optional[str] = None
    fallback_used: bool = True
    retry_suggested: bool = True


class HistoryResponse(BaseModel):
    session_id: str
    message_count: int
    messages: List[ChatMessage]
    error_summary: dict


class HealthResponse(BaseModel):
    status: str
    message: str
    api_status: dict
    error_counts: dict


class DiagnosticsSession(BaseModel):
    session_id: str
    message_count: int
    last_activity: float
    error_count: int


class DiagnosticsResponse(BaseModel):
    system_status: dict
    error_statistics: dict
    active_sessions: List[DiagnosticsSession]


