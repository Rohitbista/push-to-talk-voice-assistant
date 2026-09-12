# services/stt.py

from groq import Groq
from ptt_voice_assistant.config.settings import GROQ_API_KEY, AUDIO_TO_TEXT_MODEL

client = Groq(api_key=GROQ_API_KEY)


def transcribe_audio(
    audio_data: bytes,
    filename: str,
) -> str:

    transcription = client.audio.transcriptions.create(
        file=(filename, audio_data),
        model=AUDIO_TO_TEXT_MODEL,
        language="en",
        response_format="json",
    )

    return transcription.text