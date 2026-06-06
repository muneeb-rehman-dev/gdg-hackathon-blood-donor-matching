"""
Donor Response Classifier Agent

Uses Claude Haiku 4.5 with structured output to classify donor reply text
into: accepted / rejected / unavailable.
Fast and cheap — called for every simulated donor response.
"""

import json
from pydantic import BaseModel
from app.agents.client import get_client

MODEL = "claude-haiku-4-5"

SYSTEM_PROMPT = """You are classifying blood donor responses in a matching system.
Given a donor's reply text (may be English, Urdu, or Roman Urdu), classify their intent.

Intent options:
- accepted: donor agrees to donate (haan, yes, okay, aa raha hoon, zaroor)
- rejected: donor declines (nahi, no, nahi kar sakta, busy)
- unavailable: donor is ill, out of city, has conditions preventing donation

Return JSON with intent and confidence (0.0 to 1.0)."""

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {"type": "string", "enum": ["accepted", "rejected", "unavailable"]},
        "confidence": {"type": "number"},
    },
    "required": ["intent", "confidence"],
}


class IntentClassification(BaseModel):
    intent: str
    confidence: float


async def classify_donor_response(response_text: str) -> IntentClassification:
    client = get_client()

    response = await client.messages.create(
        model=MODEL,
        max_tokens=128,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": response_text}],
        output_config={
            "format": {
                "type": "json_schema",
                "name": "intent_classification",
                "schema": RESPONSE_SCHEMA,
                "strict": True,
            }
        },
    )

    text_content = next(
        (block.text for block in response.content if hasattr(block, "text")),
        '{"intent": "unavailable", "confidence": 0.5}',
    )
    data = json.loads(text_content)
    return IntentClassification(**data)
