from fastapi import FastAPI, File, UploadFile
import uvicorn
from typing import Annotated
import base64

from ptt_voice_assistant.services.speech_to_text import transcribe_audio
from ptt_voice_assistant.services.llm_intelligence import generate_response
from ptt_voice_assistant.services.text_to_speech import text_to_speech

app = FastAPI()

@app.post("/api/v1/chat")
async def chat(
    audio: Annotated[UploadFile, File()],
):

    # -------------------------
    # 1. Read uploaded audio
    # -------------------------

    audio_data = await audio.read()

    # -------------------------
    # 2. Speech → Text
    # -------------------------

    user_text = transcribe_audio(
        audio_data,
        audio.filename or "audio.webm",
    )

    # -------------------------
    # 3. Text → LLM → Text
    # -------------------------

    assistant_text = generate_response(
        user_text
    )

    # -------------------------
    # 4. Text → Speech
    # -------------------------

    response_audio = text_to_speech(
        assistant_text
    )

    # -------------------------
    # 5. Audio → Base64
    # -------------------------

    audio_base64 = base64.b64encode(
        response_audio
    ).decode("utf-8")

    # -------------------------
    # 6. Return response
    # -------------------------

    return {
        "user_text": user_text,
        "assistant_text": assistant_text,
        "audio_base64": audio_base64,
    }

@app.get("/")
def root():
    return {"message": "Voice Assistant Server is up and running"}

def main():
    host = "0.0.0.0"
    port = 8000
    uvicorn.run(
        "ptt_voice_assistant.app.server:app",
        host=host,
        port=port,
        reload=False,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )