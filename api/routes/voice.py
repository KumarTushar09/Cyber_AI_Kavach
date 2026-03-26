from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response

from api.schemas.response_schema import APIResponse
from services.llm_service import generate_completion
from services.sarvam_service import synthesize_speech, transcribe_audio

router = APIRouter(tags=["voice"])


_LANGUAGE_NAMES = {
    "en": "English",
    "en-IN": "English",
    "hi": "Hindi",
    "hi-IN": "Hindi",
    "ta": "Tamil",
    "ta-IN": "Tamil",
    "te": "Telugu",
    "te-IN": "Telugu",
    "kn": "Kannada",
    "kn-IN": "Kannada",
    "ml": "Malayalam",
    "ml-IN": "Malayalam",
    "bn": "Bengali",
    "bn-IN": "Bengali",
    "gu": "Gujarati",
    "gu-IN": "Gujarati",
    "mr": "Marathi",
    "mr-IN": "Marathi",
    "pa": "Punjabi",
    "pa-IN": "Punjabi",
    "ur": "Urdu",
    "ur-IN": "Urdu",
}


@router.post("/voice/transcribe", response_model=APIResponse)
async def voice_transcribe(audio: UploadFile = File(...)) -> APIResponse:
    trace_id = str(uuid4())
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(
            status_code=400,
            detail={"code": "EMPTY_AUDIO", "message": "No audio payload received."},
        )

    stt_result = await transcribe_audio(
        audio_bytes,
        file_name=audio.filename or "voice.webm",
        mime_type=audio.content_type or "audio/webm",
    )
    transcript = stt_result.get("transcript", "").strip() if isinstance(stt_result, dict) else ""
    if not transcript:
        raise HTTPException(
            status_code=502,
            detail={
                "code": "STT_FAILED",
                "message": stt_result.get("reason", "Unable to transcribe audio.")
                if isinstance(stt_result, dict)
                else "Unable to transcribe audio.",
            },
        )

    return APIResponse(
        trace_id=trace_id,
        data={
            "text": transcript,
            "stt": {
                "status": stt_result.get("status", "error") if isinstance(stt_result, dict) else "error",
                "target_url": stt_result.get("target_url") if isinstance(stt_result, dict) else None,
            },
        },
    )


@router.post("/voice/tts")
async def voice_tts(payload: dict) -> Response:
    text = str(payload.get("text", "")).strip()
    target_language_code = str(payload.get("target_language_code", "")).strip()
    if not text:
        raise HTTPException(status_code=400, detail={"code": "EMPTY_TEXT", "message": "Text is required for synthesis."})

    tts_result = await synthesize_speech(text, language_override=target_language_code or None)
    audio_bytes = tts_result.get("audio") if isinstance(tts_result, dict) else None
    content_type = tts_result.get("content_type", "audio/mpeg") if isinstance(tts_result, dict) else "audio/mpeg"

    if not audio_bytes:
        raise HTTPException(
            status_code=502,
            detail={
                "code": "TTS_FAILED",
                "message": tts_result.get("reason", "Unable to synthesize speech.")
                if isinstance(tts_result, dict)
                else "Unable to synthesize speech.",
            },
        )

    return Response(content=audio_bytes, media_type=content_type)


@router.post("/voice/translate", response_model=APIResponse)
async def voice_translate(payload: dict) -> APIResponse:
    trace_id = str(uuid4())
    text = str(payload.get("text", "")).strip()
    target_language_code = str(payload.get("target_language_code", "")).strip() or "en"

    if not text:
        raise HTTPException(status_code=400, detail={"code": "EMPTY_TEXT", "message": "Text is required for translation."})

    normalized = target_language_code
    if normalized.lower() in {"en", "en-in"}:
        return APIResponse(trace_id=trace_id, data={"text": text, "language_code": normalized})

    language_name = _LANGUAGE_NAMES.get(normalized, _LANGUAGE_NAMES.get(normalized.lower(), normalized))
    prompt = (
        f"Translate the following content to {language_name}. "
        "Preserve the original meaning, numbers, URLs, and line breaks. "
        "Return only the translated text without additional commentary.\n\n"
        f"{text}"
    )

    llm_result = await generate_completion(prompt, prompt_type="translation")
    data = llm_result.get("data") if isinstance(llm_result, dict) else None
    translated = ""
    if isinstance(data, dict):
        translated = str(data.get("response") or "").strip()

    if not translated:
        reason = llm_result.get("reason", "Unable to translate text.") if isinstance(llm_result, dict) else "Unable to translate text."
        raise HTTPException(status_code=502, detail={"code": "TRANSLATION_FAILED", "message": reason})

    return APIResponse(trace_id=trace_id, data={"text": translated, "language_code": normalized})