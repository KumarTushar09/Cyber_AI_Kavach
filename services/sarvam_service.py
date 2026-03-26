import base64
from typing import Any

import httpx

from backend.config import settings
from services.retry import retry_async


def _auth_headers() -> dict[str, str]:
    api_key = settings.SARVAM_API_KEY.strip()
    if not api_key:
        return {}

    header_name = settings.SARVAM_AUTH_HEADER.strip() or "Authorization"
    scheme = settings.SARVAM_AUTH_SCHEME.strip()
    value = f"{scheme} {api_key}".strip() if scheme else api_key
    return {header_name: value}


def _endpoint(path: str) -> str:
    base_url = settings.SARVAM_BASE_URL.strip()
    if not base_url:
        return ""
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def _extract_transcript(payload: dict[str, Any]) -> str:
    candidates = [
        payload.get("transcript"),
        payload.get("text"),
        (payload.get("data") or {}).get("transcript") if isinstance(payload.get("data"), dict) else None,
        (payload.get("data") or {}).get("text") if isinstance(payload.get("data"), dict) else None,
    ]
    for value in candidates:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _extract_embedding(payload: dict[str, Any]) -> list[float]:
    vectors: Any = payload.get("embedding")
    if vectors is None and isinstance(payload.get("data"), dict):
        vectors = payload["data"].get("embedding")
    if vectors is None and isinstance(payload.get("data"), list) and payload["data"]:
        first = payload["data"][0]
        if isinstance(first, dict):
            vectors = first.get("embedding")
    if isinstance(vectors, list):
        return [float(v) for v in vectors]
    return []


def _codec_from_mime(mime_type: str) -> str:
    normalized = (mime_type or "").lower()
    if "opus" in normalized:
        return "opus"
    if "webm" in normalized:
        return "webm"
    if "wav" in normalized or "wave" in normalized:
        return "wav"
    if "mpeg" in normalized or "mp3" in normalized:
        return "mp3"
    return "opus"


def _normalize_mime_type(mime_type: str) -> str:
    # Browsers often send values like "audio/webm;codecs=opus".
    # Sarvam STT expects the base media type, without parameters.
    base = (mime_type or "").split(";", 1)[0].strip().lower()
    return base or "audio/webm"


async def transcribe_audio(audio_bytes: bytes, file_name: str = "voice.webm", mime_type: str = "audio/webm") -> dict[str, Any]:
    target_url = _endpoint(settings.SARVAM_STT_PATH)
    if not target_url:
        return {"status": "skipped", "reason": "SARVAM_BASE_URL is not configured."}

    headers = _auth_headers()
    model = settings.SARVAM_STT_MODEL.strip()
    language = settings.SARVAM_STT_LANGUAGE.strip()
    normalized_mime_type = _normalize_mime_type(mime_type)
    input_codec = _codec_from_mime(normalized_mime_type)

    async def _send_once() -> dict[str, Any]:
        data: dict[str, str] = {"mode": "translate", "input_audio_codec": input_codec}
        if model:
            data["model"] = model
        if language:
            data["language_code"] = language
            # Keep legacy field for compatibility with older gateway deployments.
            data["language"] = language

        files = {"file": (file_name, audio_bytes, normalized_mime_type)}
        async with httpx.AsyncClient(timeout=settings.SARVAM_TIMEOUT_SECONDS, headers=headers) as client:
            response = await client.post(target_url, data=data, files=files)
            if response.status_code >= 400:
                detail = response.text
                raise httpx.HTTPStatusError(
                    f"{response.status_code} response from Sarvam STT: {detail}",
                    request=response.request,
                    response=response,
                )
            payload = response.json()
            transcript = _extract_transcript(payload)
            return {
                "status": "ok",
                "target_url": target_url,
                "data": payload,
                "transcript": transcript,
            }

    try:
        return await retry_async(
            _send_once,
            attempts=settings.RETRY_MAX_ATTEMPTS,
            base_delay_seconds=settings.RETRY_BASE_DELAY_SECONDS,
            retry_on=(httpx.RequestError, httpx.HTTPStatusError),
        )
    except Exception as exc:
        return {"status": "error", "target_url": target_url, "reason": str(exc)}


async def embed_text_via_sarvam(text: str) -> dict[str, Any]:
    target_url = _endpoint(settings.SARVAM_EMBED_PATH)
    if not target_url:
        return {"status": "skipped", "reason": "SARVAM_BASE_URL is not configured."}

    headers = {"Content-Type": "application/json", **_auth_headers()}
    model = settings.SARVAM_EMBED_MODEL.strip()
    payload: dict[str, Any] = {"input": text}
    if model:
        payload["model"] = model

    async def _send_once() -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=settings.SARVAM_TIMEOUT_SECONDS) as client:
            response = await client.post(target_url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            embedding = _extract_embedding(data)
            return {
                "status": "ok",
                "target_url": target_url,
                "data": data,
                "embedding": embedding,
            }

    try:
        return await retry_async(
            _send_once,
            attempts=settings.RETRY_MAX_ATTEMPTS,
            base_delay_seconds=settings.RETRY_BASE_DELAY_SECONDS,
            retry_on=(httpx.RequestError, httpx.HTTPStatusError),
        )
    except Exception as exc:
        return {"status": "error", "target_url": target_url, "reason": str(exc)}


def _extract_audio_b64(payload: dict[str, Any]) -> str:
    audios = payload.get("audios")
    if isinstance(audios, list):
        for item in audios:
            if isinstance(item, str) and item.strip():
                return item.strip()

    nested_data = payload.get("data")
    if isinstance(nested_data, dict):
        nested_audios = nested_data.get("audios")
        if isinstance(nested_audios, list):
            for item in nested_audios:
                if isinstance(item, str) and item.strip():
                    return item.strip()

    candidates = [
        payload.get("audio"),
        payload.get("audio_base64"),
        payload.get("audioContent"),
        (payload.get("data") or {}).get("audio") if isinstance(payload.get("data"), dict) else None,
        (payload.get("data") or {}).get("audio_base64") if isinstance(payload.get("data"), dict) else None,
        (payload.get("data") or {}).get("audioContent") if isinstance(payload.get("data"), dict) else None,
    ]
    for value in candidates:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


async def synthesize_speech(text: str, language_override: str = None) -> dict[str, Any]:
    target_url = _endpoint(settings.SARVAM_TTS_PATH)
    if not target_url:
        return {"status": "skipped", "reason": "SARVAM_BASE_URL is not configured."}

    model = settings.SARVAM_TTS_MODEL.strip()
    default_language = settings.SARVAM_TTS_LANGUAGE.strip()
    language = language_override if language_override else default_language
    voice = settings.SARVAM_TTS_VOICE.strip()
    audio_format = settings.SARVAM_TTS_FORMAT.strip() or "mp3"

    payload: dict[str, Any] = {
        "text": text,
        "target_language_code": language,
        "output_audio_format": audio_format,
    }
    if model:
        payload["model"] = model
    if voice:
        payload["speaker"] = voice

    headers = {"Content-Type": "application/json", **_auth_headers()}

    async def _send_once() -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=settings.SARVAM_TIMEOUT_SECONDS) as client:
            response = await client.post(target_url, headers=headers, json=payload)
            response.raise_for_status()

            content_type = (response.headers.get("content-type") or "").split(";")[0].strip().lower()
            if content_type.startswith("audio/"):
                return {
                    "status": "ok",
                    "target_url": target_url,
                    "audio": response.content,
                    "content_type": content_type,
                }

            data = response.json()
            audio_b64 = _extract_audio_b64(data)
            if audio_b64:
                return {
                    "status": "ok",
                    "target_url": target_url,
                    "audio": base64.b64decode(audio_b64),
                    "content_type": f"audio/{audio_format}",
                    "data": data,
                }

            return {
                "status": "error",
                "target_url": target_url,
                "reason": "No audio content in TTS response.",
                "data": data,
            }

    try:
        return await retry_async(
            _send_once,
            attempts=settings.RETRY_MAX_ATTEMPTS,
            base_delay_seconds=settings.RETRY_BASE_DELAY_SECONDS,
            retry_on=(httpx.RequestError, httpx.HTTPStatusError),
        )
    except Exception as exc:
        return {"status": "error", "target_url": target_url, "reason": str(exc)}

