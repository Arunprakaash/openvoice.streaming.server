import logging
import torch
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from openvoice_streaming_server.core.libs import StreamingBaseSpeakerTTS
from openvoice_streaming_server.core.schemas import SynthesisRequest, SynthesisResponse

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
            response = SynthesisResponse(audio_chunk=audio_chunk)
            await websocket.send_bytes(response.audio_chunk)
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
        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.close()
            self.connections.remove(websocket)

    async def handle_websocket(self, websocket: WebSocket):
        await self.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                request = SynthesisRequest.parse_raw(data)
                if request.text == "":
                    await self.disconnect(websocket)
                    return
                text = request.text
                speaker = request.speaker
                language = request.language
                speed = request.speed
                logger.info(f"Received text: {text}, speaker: {speaker}, language: {language}, speed: {speed}")
                audio_stream = self.model.tts_stream(text, speaker, language, speed)
                await send_audio_stream(websocket, audio_stream)
        except WebSocketDisconnect:
            await self.disconnect(websocket)
        except Exception as e:
            logger.error(f"Error during text synthesis: {e}")
            await self.disconnect(websocket)


en_checkpoint_base = "../resources/checkpoints/base_speakers/EN"
device = "cuda:0" if torch.cuda.is_available() else "cpu"

# Load models and resources
model = StreamingBaseSpeakerTTS(f'{en_checkpoint_base}/config.json', device=device)
model.load_ckpt(f'{en_checkpoint_base}/checkpoint.pth')

handler = WebSocketHandler(model)


@router.websocket("/synthesize")
async def synthesize(websocket: WebSocket):
    await handler.handle_websocket(websocket)
