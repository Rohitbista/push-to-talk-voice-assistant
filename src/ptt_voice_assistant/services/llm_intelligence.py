# services/llm.py

from groq import Groq
from ptt_voice_assistant.config.settings import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)


def generate_response(user_text: str) -> str:

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
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