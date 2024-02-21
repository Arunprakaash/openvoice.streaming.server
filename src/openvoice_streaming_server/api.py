from fastapi import FastAPI

from openvoice_streaming_server.routers import synthesize

app = FastAPI()

routers = synthesize.router
app.include_router(routers, prefix="/v1")
