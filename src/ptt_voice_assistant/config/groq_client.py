from groq import AsyncGroq
from .settings import GROQ_API_KEY

client = AsyncGroq(api_key=GROQ_API_KEY)