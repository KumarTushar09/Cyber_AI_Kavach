from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from api.schemas.response_schema import APIResponse
from backend.auth import require_scopes
from services.rag_service import query_rag
from services.sarvam_service import transcribe_audio

router = APIRouter(tags=["knowledge"], dependencies=[Depends(require_scopes("knowledge:read"))])


@router.post("/knowledge/voice", response_model=APIResponse)
async def query_knowledge_voice(audio: UploadFile = File(...)) -> APIResponse:
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
                "message": stt_result.get("reason", "Unable to transcribe audio.") if isinstance(stt_result, dict) else "Unable to transcribe audio.",
            },
        )

    rag_result = await query_rag(transcript)
    answer = str(rag_result.get("answer", ""))

    return APIResponse(
        trace_id=trace_id,
        data={
            "question": transcript,
            "answer": answer,
            "rag": rag_result,
            "stt": {
                "status": stt_result.get("status", "error") if isinstance(stt_result, dict) else "error",
                "target_url": stt_result.get("target_url") if isinstance(stt_result, dict) else None,
            },
        },
    )