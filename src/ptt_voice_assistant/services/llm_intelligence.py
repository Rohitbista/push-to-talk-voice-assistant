# services/llm.py
from ptt_voice_assistant.config.settings import LLM_MODEL
from ptt_voice_assistant.config.groq_client import client

async def generate_response(user_text: str) -> str:

    response = await client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful voice assistant. "
                    "Keep responses concise and natural "
                    "for spoken conversation."
                ),
            },
            {
                "role": "user",
                "content": user_text,
            },
        ],
    )

    return response.choices[0].message.content