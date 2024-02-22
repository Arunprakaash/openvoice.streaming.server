from pydantic import BaseModel
from typing import Optional, Text


class SynthesisRequest(BaseModel):
    text: Text
    speaker: Optional[Text] = 'default'
    language: Optional[Text] = 'english'
    speed: Optional[float] = 1.0


class SynthesisResponse(BaseModel):
    audio_chunk: bytes
