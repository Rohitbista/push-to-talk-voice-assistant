# services/tts.py

# from io import BytesIO

# from gtts import gTTS

# def text_to_speech(text: str) -> bytes:
#     audio = BytesIO()
#     tts = gTTS(
#         text=text,
#         lang="en",
#     )
#     tts.write_to_fp(audio)
#     return audio.getvalue()

# Another method to do it faster then gtts
# Imp: Sometime working but sometime not working
# import edge_tts

# async def text_to_speech_bytes(text: str, voice: str = "en-US-AvaNeural") -> bytes:
#     communicate = edge_tts.Communicate(text, voice)
#     audio_data = bytearray()

#     async for chunk in communicate.stream():
#         if chunk["type"] == "audio":
#             audio_data.extend(chunk["data"])

#     return bytes(audio_data)


# using piper-tts and doing the same thing
from io import BytesIO
import wave

from piper import PiperVoice


#voice = PiperVoice.load("voices/en_US-amy-medium.onnx")
voice = PiperVoice.load("voices/en_US-lessac-high.onnx")


def text_to_speech(text: str) -> bytes:
    audio = BytesIO()

    with wave.open(audio, "wb") as wav_file:
        voice.synthesize_wav(text, wav_file)

    return audio.getvalue()

# Used it to test that's all
# if __name__ == "__main__":
#     audio = text_to_speech("Hello")

#     print(f"Generated {len(audio)} bytes")

#     with open("test.wav", "wb") as f:
#         f.write(audio)




import re

def strip_markdown(text: str) -> str:
    """
    Remove markdown formatting so the text reads naturally when spoken.
    The original formatted text is preserved separately for chat history.
    """
    # Code fences first (before inline-code so ``` isn't partially stripped)
    text = re.sub(r"```[\s\S]*?```", "", text)
    # Inline code: `code` → code
    text = re.sub(r"`(.+?)`", r"\1", text)
    # Headers: ## Heading → Heading
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Bold / italic: **text**, *text*, __text__, _text_
    text = re.sub(r"\*{1,2}(.+?)\*{1,2}", r"\1", text)
    text = re.sub(r"_{1,2}(.+?)_{1,2}", r"\1", text)
    # Links: [label](url) → label
    text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)
    # Bullet / numbered list markers at line start
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)
    # Horizontal rules
    text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)
    # Collapse extra blank lines left by removed blocks
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()