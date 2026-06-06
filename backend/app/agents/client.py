import google.generativeai as genai
from app.config import settings

_configured = False


def get_client() -> genai:
    global _configured
    if not _configured:
        genai.configure(api_key=settings.gemini_api_key)
        _configured = True
    return genai
