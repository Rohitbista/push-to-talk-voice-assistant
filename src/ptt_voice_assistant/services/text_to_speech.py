# services/tts.py
import edge_tts

from io import BytesIO

from gtts import gTTS

def text_to_speech(text: str) -> bytes:
    audio = BytesIO()
    tts = gTTS(
        text=text,
        lang="en",
    )
    tts.write_to_fp(audio)
    return audio.getvalue()

# Another method to do it faster then gtts
# Imp: Sometime working but sometime not working
async def text_to_speech_bytes(text: str, voice: str = "en-US-AvaNeural") -> bytes:
    communicate = edge_tts.Communicate(text, voice)
    audio_data = bytearray()

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data.extend(chunk["data"])

    return bytes(audio_data)