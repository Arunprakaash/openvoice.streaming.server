import json

import torch
from fastapi import WebSocket, APIRouter
from starlette.websockets import WebSocketDisconnect

from src.openvoice_streaming_server.openvoice import StreamingBaseSpeakerTTS

router = APIRouter()

en_checkpoint_base = "./checkpoints/base_speakers/EN"
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load models and resources
en_base_speaker_tts = StreamingBaseSpeakerTTS(f'{en_checkpoint_base}/config.json', device=device)
model = en_base_speaker_tts.load_ckpt(f'{en_checkpoint_base}/checkpoint.pth')  # Initialize your TTS class instance here


@router.websocket("/synthesize")
async def synthesize(websocket: WebSocket):
    await websocket.accept()
    while True:
        try:
            data = await websocket.receive_text()
            data = json.loads(data)
            text = data['text']
            speaker = data.get('speaker')
            language = data.get('language')
            speed = data.get('speed', 1.0)
            audio_stream = model.tts_stream(text, speaker, language, speed)
            async for audio_chunk in audio_stream:
                await websocket.send_bytes(audio_chunk)
        except WebSocketDisconnect:
            break
