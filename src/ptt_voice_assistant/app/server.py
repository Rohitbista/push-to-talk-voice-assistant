import time
from fastapi import FastAPI, File, UploadFile
import uvicorn
from typing import Annotated
import base64
from fastapi.middleware.cors import CORSMiddleware

from ptt_voice_assistant.services.speech_to_text import transcribe_audio
from ptt_voice_assistant.services.llm_intelligence import generate_response
from ptt_voice_assistant.services.text_to_speech import text_to_speech, text_to_speech_bytes

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500"],  # dev server port,http://localhost:5500
    allow_methods=["*"],
    allow_headers=["*"],
)

MIME_TO_EXT = {
    "audio/webm": "webm",
    "audio/ogg":  "ogg",
    "audio/mp4":  "mp4",
    "audio/mpeg": "mp3",
    "audio/wav":  "wav",
}

@app.post("/api/v1/chat")
async def chat(
    audio: Annotated[UploadFile, File()],
):
    start = time.monotonic()
    try:

        # -------------------------
        # 1. Read uploaded audio
        # -------------------------

        audio_data = await audio.read()

        # Derive a reliable extension from Content-Type, ignoring whatever
        # filename the client sent.
        content_type = (audio.content_type or "").split(";")[0].strip()
        ext = MIME_TO_EXT.get(content_type, "webm")
        safe_filename = f"audio.{ext}"

        # -------------------------
        # 2. Speech → Text
        # -------------------------

        user_text = await transcribe_audio(audio_data, safe_filename)

        # -------------------------
        # 3. Text → LLM → Text
        # -------------------------

        assistant_text = await generate_response(
            user_text
        )

        # -------------------------
        # 4. Text → Speech
        # -------------------------
        response_audio = await text_to_speech_bytes(assistant_text)

        # -------------------------
        # 5. Audio → Base64
        # -------------------------

        audio_base64 = base64.b64encode(
            response_audio
        ).decode("utf-8")

        response_time_ms = round((time.monotonic() - start) * 1000, 2)

        # -------------------------
        # 6. Return response
        # -------------------------

        return {
            "success": True,
            "message": "Audio successfully processed",
            "response_time_ms": response_time_ms,
            "user_text": user_text,
            "assistant_text": assistant_text,
            "audio_base64": audio_base64,
        }
    except Exception as e:
        response_time_ms = round((time.monotonic() - start) * 1000, 2)
        return {"success": False, "message": "Something went wrong", "response_time_ms": response_time_ms, "error": str(e)}

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
        loop="asyncio",   # ← explicitly use the policy we set above
    )