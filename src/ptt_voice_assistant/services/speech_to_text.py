# services/stt.py

from groq import Groq
from ptt_voice_assistant.config.settings import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)


def transcribe_audio(
    audio_data: bytes,
    filename: str,
) -> str:

    transcription = client.audio.transcriptions.create(
        file=(filename, audio_data),
        model="whisper-large-v3-turbo",
        language="en",
        response_format="json",
    )

    return transcription.text