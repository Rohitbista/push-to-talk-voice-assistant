# services/tts.py
import edge_tts

# Another method to do it faster then gtts
async def text_to_speech_bytes(text: str, voice: str = "en-US-AvaNeural") -> bytes:
    communicate = edge_tts.Communicate(text, voice)
    audio_data = bytearray()

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data.extend(chunk["data"])

    return bytes(audio_data)