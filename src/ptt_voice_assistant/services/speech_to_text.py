# services/stt.py
from ptt_voice_assistant.config.settings import AUDIO_TO_TEXT_MODEL
from ptt_voice_assistant.config.groq_client import client

async def transcribe_audio(
    audio_data: bytes,
    filename: str,
) -> str:

    transcription = await client.audio.transcriptions.create(
        file=(filename, audio_data),
        model=AUDIO_TO_TEXT_MODEL,
        language="en",
        response_format="json",
    )

    return transcription.text