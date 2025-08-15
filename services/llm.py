from typing import Optional, Tuple

import requests
import google.generativeai as genai

from schemas.models import ErrorType

_GENAI_CONFIGURED = False


def generate_response(prompt: str, session_id: str, logger, api_configured: bool) -> Tuple[bool, str, Optional[ErrorType]]:
    """Robust LLM response with Gemini. Returns (success, text, error)."""
    if not api_configured:
        return False, "", ErrorType.CONFIG_ERROR

    global _GENAI_CONFIGURED
    if api_configured and not _GENAI_CONFIGURED:
        import os as _os
        key = _os.getenv("GEMINI_API_KEY", "")
        if key:
            genai.configure(api_key=key)
            _GENAI_CONFIGURED = True

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        if not response or not getattr(response, "text", None):
            return False, "", ErrorType.LLM_ERROR
        text = response.text.strip()
        logger.info(f"[{session_id}] LLM Success: {len(text)} characters")
        return True, text, None

    except genai.types.BlockedPromptException as e:  # type: ignore[attr-defined]
        logger.error(f"[{session_id}] LLM Blocked prompt: {e}")
        fallback = "I'm sorry, I can't respond to that type of request. Could you please ask something else?"
        return True, fallback, None
    except requests.exceptions.RequestException as e:
        logger.error(f"[{session_id}] LLM Network error: {e}")
        return False, "", ErrorType.NETWORK_ERROR
    except Exception as e:
        logger.error(f"[{session_id}] LLM Unexpected error: {e}")
        return False, "", ErrorType.LLM_ERROR


