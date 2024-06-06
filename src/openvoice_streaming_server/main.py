from fastapi import FastAPI

from openvoice_streaming_server.v1.api import api_router

app = FastAPI()

# Include API routes
app.include_router(api_router, prefix="/v1")
