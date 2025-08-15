import os
import time
from typing import Optional, Tuple

import assemblyai as aai
import requests

from schemas.models import ErrorType

_AAI_CONFIGURED = False


async def speech_to_text(file_path: str, session_id: str, logger, api_configured: bool) -> Tuple[bool, str, Optional[ErrorType]]:
    """Robust speech-to-text using AssemblyAI. Returns (success, text, error)."""
    if not api_configured:
        return False, "", ErrorType.CONFIG_ERROR

    global _AAI_CONFIGURED
    if api_configured and not _AAI_CONFIGURED:
        # Configure API key lazily to avoid side effects at import time
        import os as _os
        key = _os.getenv("ASSEMBLYAI_API_KEY", "")
        if key:
            aai.settings.api_key = key
            _AAI_CONFIGURED = True

    try:
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
            logger.error(f"[{session_id}] AssemblyAI transcription error: {transcript.error}")
            return False, "", ErrorType.STT_ERROR

        text = (transcript.text or "").strip()
        if not text:
            return False, "", ErrorType.STT_ERROR

        logger.info(f"[{session_id}] STT Success: {len(text)} characters")
        return True, text, None

    except requests.exceptions.RequestException as e:
        logger.error(f"[{session_id}] STT Network error: {e}")
        return False, "", ErrorType.NETWORK_ERROR
    except Exception as e:
        logger.error(f"[{session_id}] STT Unexpected error: {e}")
        return False, "", ErrorType.STT_ERROR


