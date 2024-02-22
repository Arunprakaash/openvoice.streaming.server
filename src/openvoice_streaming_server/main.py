from fastapi import FastAPI

from v1.api import api_router

app = FastAPI()

# Include API routes
app.include_router(api_router, prefix="/v1")
