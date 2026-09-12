import os

from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_333_API_KEY")
AUDIO_TO_TEXT_MODEL=os.getenv("AUDIO_TO_TEXT_MODEL")
LLM_MODEL=os.getenv("LLM_MODEL")