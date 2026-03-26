from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.errors import register_exception_handlers
from backend.middleware import configure_logging, request_context_middleware
# URL-only mode: keep non-URL routers commented so they can be restored later.
# from api.routes.apk_analysis import router as apk_router
# from api.routes.file_upload import router as upload_router
from api.routes.knowledge_query import router as knowledge_router
from api.routes.knowledge_voice import router as knowledge_voice_router
from api.routes.voice import router as voice_router
# from api.routes.sms_analysis import router as sms_router
from api.routes.system_health import router as system_health_router
from api.routes.url_analysis import router as url_router
# from api.routes.fraud_check import router as fraud_router

configure_logging()
app = FastAPI(title=settings.APP_NAME, version="0.1.0")
register_exception_handlers(app)
app.middleware("http")(request_context_middleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "instance-1-backend"}


app.include_router(url_router, prefix=settings.API_PREFIX)
# URL-only mode: disable non-URL API surfaces for the first phase.
# app.include_router(sms_router, prefix=settings.API_PREFIX)
# app.include_router(apk_router, prefix=settings.API_PREFIX)
app.include_router(knowledge_router, prefix=settings.API_PREFIX)
app.include_router(knowledge_voice_router, prefix=settings.API_PREFIX)
app.include_router(voice_router, prefix=settings.API_PREFIX)
# app.include_router(fraud_router, prefix=settings.API_PREFIX)
# app.include_router(upload_router, prefix=settings.API_PREFIX)
app.include_router(system_health_router, prefix=settings.API_PREFIX)
