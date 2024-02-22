from fastapi import APIRouter

from openvoice_streaming_server.v1.endpoints import synthesize

router = APIRouter()
router.include_router(synthesize.router)
api_router = APIRouter()
api_router.include_router(router, prefix="/api")
