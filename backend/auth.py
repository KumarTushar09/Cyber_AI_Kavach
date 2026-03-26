from fastapi import HTTPException, Request

from backend.config import settings


def require_scopes(*required_scopes: str):
    async def dependency(request: Request) -> None:
        if not settings.API_KEY.strip():
            return

        granted_scopes = set(getattr(request.state, "api_scopes", set()))
        if "*" in granted_scopes:
            return

        missing_scopes = [scope for scope in required_scopes if scope not in granted_scopes]
        if missing_scopes:
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "AUTH_FORBIDDEN",
                    "message": f"Missing required scope(s): {', '.join(missing_scopes)}",
                },
            )

    return dependency