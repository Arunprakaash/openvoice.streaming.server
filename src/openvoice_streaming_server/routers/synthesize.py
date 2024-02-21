import json

import torch
from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect

from openvoice_streaming_server.openvoice_stream import StreamingBaseSpeakerTTS

router = APIRouter()


async def send_audio_stream(websocket: WebSocket, audio_stream):
    async for audio_chunk in audio_stream:
        await websocket.send_bytes(audio_chunk)


class WebSocketHandler:
    def __init__(self, tts_model):
        self.model = tts_model
        self.connections = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.add(websocket)

    async def disconnect(self, websocket: WebSocket):
        self.connections.remove(websocket)

    async def handle_websocket(self, websocket: WebSocket):
        await self.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                data = json.loads(data)
                text = data.get("text")
                speaker = data.get('speaker', 'default')
                language = data.get('language', 'english')
                speed = data.get('speed', 1.0)
                audio_stream = self.model.tts_stream(text, speaker, language, speed)
                await send_audio_stream(websocket, audio_stream)
        except WebSocketDisconnect:
            await self.disconnect(websocket)
        except Exception as e:
            print(f"Error during text synthesis: {e}")
            await self.disconnect(websocket)


en_checkpoint_base = "../checkpoints/base_speakers/EN"
device = "cuda:0" if torch.cuda.is_available() else "cpu"

# Load models and resources
model = StreamingBaseSpeakerTTS(f'{en_checkpoint_base}/config.json', device=device)
model.load_ckpt(f'{en_checkpoint_base}/checkpoint.pth')

handler = WebSocketHandler(model)


@router.websocket("/synthesize")
async def synthesize(websocket: WebSocket):
    await handler.handle_websocket(websocket)
