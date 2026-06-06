"""
Request Extraction Agent — Gemini

Uses Gemini with JSON mode to extract structured blood request details
from natural language (English + Urdu/Roman Urdu).
"""

import json
import google.generativeai as genai
from app.agents.client import get_client
from app.schemas.blood_request import BloodRequestExtraction

MODEL = "gemini-2.0-flash"

SYSTEM_PROMPT = """You are an AI assistant for a blood donor matching system in Karachi, Pakistan.
Extract structured blood request information from messages in English, Urdu, or Roman Urdu.

Karachi areas: Clifton, DHA, Gulshan-e-Iqbal, Nazimabad, North Karachi, Saddar, Korangi, Malir, Lyari.

Return a JSON object with these exact fields:
- blood_group: one of A+, A-, B+, B-, AB+, AB-, O+, O- (null if not mentioned)
- units_needed: integer number of units needed (null if not mentioned)
- hospital_name: name of hospital (null if not mentioned)
- hospital_area: Karachi area (null if not mentioned)
- urgency_level: "critical", "high", "medium", or "low"
- patient_name: patient name if mentioned (null otherwise)
- needs_clarification: true if blood_group OR hospital_area is missing
- clarification_questions: list of specific questions for missing info
- extracted_successfully: true only if blood_group AND hospital_area are both present
- bot_reply: a warm, concise English reply for the chat UI"""


async def extract_blood_request(
    message: str,
    conversation_history: list[dict] | None = None,
) -> BloodRequestExtraction:
    get_client()

    model = genai.GenerativeModel(
        model_name=MODEL,
        system_instruction=SYSTEM_PROMPT,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            temperature=0.2,
        ),
    )

    # Build prompt with history context
    prompt = ""
    if conversation_history:
        for turn in conversation_history[-6:]:  # Last 3 exchanges
            role = "User" if turn["role"] == "user" else "Assistant"
            prompt += f"{role}: {turn['content']}\n"
    prompt += f"User: {message}"

    response = await model.generate_content_async(prompt)

    try:
        data = json.loads(response.text)
    except (json.JSONDecodeError, ValueError):
        data = {
            "blood_group": None,
            "units_needed": None,
            "hospital_name": None,
            "hospital_area": None,
            "urgency_level": "high",
            "patient_name": None,
            "needs_clarification": True,
            "clarification_questions": ["What blood group is needed?", "Which hospital and area?"],
            "extracted_successfully": False,
            "bot_reply": "I couldn't parse the request. Could you please specify the blood group and hospital area?",
        }

    return BloodRequestExtraction(**data)
