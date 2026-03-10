from fastapi import APIRouter

from app.api.v1.stt import stt_api

router = APIRouter()
router.include_router(stt_api.router)
