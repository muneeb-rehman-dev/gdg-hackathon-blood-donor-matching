"""
Donor Response Classifier Agent — Gemini Flash

Classifies donor reply text into: accepted / rejected / unavailable.
"""

import json
import google.generativeai as genai
from pydantic import BaseModel
from app.agents.client import get_client

MODEL = "gemini-2.0-flash"

SYSTEM_PROMPT = """Classify blood donor responses. Given a reply (English, Urdu, or Roman Urdu), return JSON:
- intent: "accepted", "rejected", or "unavailable"
- confidence: float 0.0 to 1.0

Examples:
"Haan zaroor aa raha hoon" -> accepted
"Nahi kar sakta, busy hoon" -> rejected
"Main beemaar hoon" -> unavailable"""


class IntentClassification(BaseModel):
    intent: str
    confidence: float


async def classify_donor_response(response_text: str) -> IntentClassification:
    get_client()

    model = genai.GenerativeModel(
        model_name=MODEL,
        system_instruction=SYSTEM_PROMPT,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            temperature=0.1,
        ),
    )

    response = await model.generate_content_async(response_text)

    try:
        data = json.loads(response.text)
    except (json.JSONDecodeError, ValueError):
        data = {"intent": "unavailable", "confidence": 0.5}

    return IntentClassification(**data)
