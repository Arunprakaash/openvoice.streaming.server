from fastapi import FastAPI

from openvoice_streaming_server.routers import synthesize

app = FastAPI()

routers = synthesize.router
app.include_router(routers, prefix="/v1")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, port=8000, reload=True)
