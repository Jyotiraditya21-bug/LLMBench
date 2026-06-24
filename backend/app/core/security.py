from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from backend.app.core.config import settings

# Setup standard header extractor
api_key_header = APIKeyHeader(name=settings.API_KEY_NAME, auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """Dependency validator to verify active API Token in headers.

    Allows integration of EvalForge into automated CI pipelines securely.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Authentication credentials missing from header: {settings.API_KEY_NAME}",
        )
    if api_key != settings.EVALFORGE_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access Denied: Invalid API Key token",
        )
    return api_key
