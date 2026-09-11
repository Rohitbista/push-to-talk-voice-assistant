# services/tts.py

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