import base64
import io
from typing import Optional, Tuple

import httpx

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except Exception:
    GTTS_AVAILABLE = False

from schemas.models import ErrorType


def _generate_fallback_audio(text: str, logger) -> str:
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


async def text_to_speech(text: str, voice_id: str, session_id: str, logger, murf_configured: bool) -> Tuple[bool, str, Optional[ErrorType]]:
    if not murf_configured:
        logger.warning(f"[{session_id}] No Murf API key, using fallback TTS")
        return True, _generate_fallback_audio(text, logger), None

    if len(text) > 3000:
        text = text[:2950] + "..."

    murf_api_url = "https://api.murf.ai/v1/speech/generate"

    async def attempt_murf_request(headers: dict, payload: dict):
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
        },
    ]

    # Caller passes headers to try

    return_fallback = None
    for headers in []:
        pass

    # Note: fetch at call time to avoid import side-effects
    import os
    murf_key = os.getenv("MURF_API_KEY", "")
    header_variants = [
        {"Authorization": f"Bearer {murf_key}", "Content-Type": "application/json"},
        {"api-key": murf_key, "Content-Type": "application/json"},
    ]

    for headers in header_variants:
        for payload in payload_variants:
            success, data = await attempt_murf_request(headers, payload)
            if success:
                result = data
                audio_url = result.get("audioFile") or result.get("url") or result.get("audioUrl")
                if audio_url:
                    logger.info(f"[{session_id}] Murf TTS Success")
                    return True, audio_url, None
                audio_data = result.get("audioData") or result.get("audioBase64")
                if audio_data:
                    logger.info(f"[{session_id}] Murf TTS Success (base64)")
                    return True, f"data:audio/mp3;base64,{audio_data}", None

    logger.warning(f"[{session_id}] Murf API failed, falling back to gTTS")
    return True, _generate_fallback_audio(text, logger), None


