import asyncio
import json
import numpy as np
import sounddevice as sd
import websockets

from chain import chain  # Assuming chain module is correctly imported


async def stream(audio_stream):
    """Receive audio data and process it."""
    if audio_stream:
        audio_data = np.frombuffer(audio_stream, dtype=np.float32)
        sd.play(audio_data, samplerate=22050)
        sd.wait()


async def synthesize_text(text):
    uri = "ws://localhost:8000/v1/api/synthesize"

    async with websockets.connect(uri, max_size=None) as websocket:

        async def listen():
            """Listen to the websocket for audio data and stream it."""
            while True:
                try:
                    data = await websocket.recv()
                    await stream(data)
                except websockets.exceptions.ConnectionClosed:
                    print("Connection closed")
                    break

        listen_task = asyncio.create_task(listen())

        await websocket.send(json.dumps({
            "text": text,
            "speaker": "default",
            "language": "english",
            "speed": 1.0
        }))

        await listen_task


async def llm_chain(query: str):
    """Retrieve text from OpenAI and pass it to the text-to-speech function."""
    response = chain.invoke({'input': query})
    await synthesize_text(response.content)


if __name__ == "__main__":
    while True:
        user_query = input("input_query: ")
        if user_query.lower() == "exit":
            break
        asyncio.run(llm_chain(user_query))
