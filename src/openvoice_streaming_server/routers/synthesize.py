"""
This module provides a WebSocket-based API for real-time text-to-speech synthesis.

Classes:
    WebSocketHandler: Handles WebSocket connections and text synthesis requests.
Functions:
    synthesize: WebSocket route for initiating text synthesis.

Usage:
    1. Initialize WebSocketHandler with a TTS model.
    2. Connect to the "/synthesize" route using a WebSocket client.
    3. Send JSON data with text, speaker, language, and speed information to initiate synthesis.
    4. Receive synthesized audio stream in real-time.

Example:
    WebSocket client sends JSON data:
        {
            "text": "Hello, how are you?",
            "speaker": "default",
            "language": "english",
            "speed": 1.0
        }
    WebSocket server responds with audio stream synthesized from the text input.
"""

import json
import logging
import torch
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from openvoice_streaming_server.openvoice_stream import StreamingBaseSpeakerTTS

router = APIRouter()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


async def send_audio_stream(websocket: WebSocket, audio_stream):
    try:
        async for audio_chunk in audio_stream:
            await websocket.send_bytes(audio_chunk)
    except WebSocketDisconnect:
        pass


class WebSocketHandler:
    def __init__(self, tts_model):
        self.model = tts_model
        self.connections = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.add(websocket)

    async def disconnect(self, websocket: WebSocket):
        await websocket.close()
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
                logger.info(f"Received text: {text}, speaker: {speaker}, language: {language}, speed: {speed}")
                audio_stream = self.model.tts_stream(text, speaker, language, speed)
                await send_audio_stream(websocket, audio_stream)
        except WebSocketDisconnect:
            await self.disconnect(websocket)
        except Exception as e:
            logger.error(f"Error during text synthesis: {e}")
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
