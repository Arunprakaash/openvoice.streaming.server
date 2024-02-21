import asyncio
import json

import numpy as np
import sounddevice as sd
import websockets
from chain import chain  # Assuming chain module is correctly imported


async def text_chunker(chunks):
    """Split text into chunks, ensuring not to break sentences."""
    splitters = (".", ",", "?", "!", ";", ":", "—", "-", "(", ")", "[", "]", "}", " ")
    buffer = ""
    if chunks:
        async for text in chunks:
            if buffer.endswith(splitters):
                yield buffer + " "
                buffer = text
            elif text.startswith(splitters):
                yield buffer + text[0] + " "
                buffer = text[1:]
            else:
                buffer += text
        if buffer:
            yield buffer + " "


async def text_generation(query):
    async for event in chain.astream_events({"input": query}, version="v1"):
        if event["event"] == "on_chat_model_stream" and event["data"]["chunk"].content:
            yield event["data"]["chunk"].content


async def synthesize_text(query):
    async with websockets.connect("ws://localhost:8000/v1/synthesize") as websocket:
        async for chunk in text_chunker(text_generation(query)):
            await websocket.send(json.dumps({
                "text": chunk,
                "speaker": "default",
                "language": "english",
                "speed": 1.0
            }))

            # Receive and play streaming audio data
            audio_chunk = await websocket.recv()
            # Play the audio chunk using sounddevice
            audio_data = np.frombuffer(audio_chunk, dtype=np.float32)
            sd.play(audio_data, samplerate=22050)
            sd.wait()


async def main():
    query = input("Enter query: ")
    await synthesize_text(query)


# Run the asyncio event loop
if __name__ == "__main__":
    asyncio.run(main())
