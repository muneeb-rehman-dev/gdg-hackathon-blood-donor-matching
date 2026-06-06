"""
Request Extraction Agent

Uses Claude Opus 4.8 with structured output (messages.parse) to extract
blood request details from natural language — English and Urdu/Roman Urdu.
Returns a BloodRequestExtraction Pydantic model.
"""

import json
from app.agents.client import get_client
from app.schemas.blood_request import BloodRequestExtraction

MODEL = "claude-opus-4-8"

SYSTEM_PROMPT = """You are an AI assistant for a blood donor matching system in Karachi, Pakistan.
Your task is to extract structured blood request information from messages written in English,
Urdu, or Roman Urdu (Urdu written in English letters).

Karachi areas to recognise: Clifton, DHA, Gulshan-e-Iqbal, Nazimabad, North Karachi, Saddar, Korangi, Malir, Lyari.

Extract:
- blood_group: one of A+, A-, B+, B-, AB+, AB-, O+, O- (null if not mentioned)
- units_needed: number of units/bags/bottles needed (default 1 if emergency but not specified)
- hospital_name: name of the hospital (null if not mentioned)
- hospital_area: Karachi area of the hospital (null if not mentioned)
- urgency_level: critical / high / medium / low (infer from words like "emergency", "urgent", "zaroorat")
- patient_name: patient's name if mentioned (null otherwise)
- needs_clarification: true if blood_group OR hospital_area is missing (these are critical)
- clarification_questions: list of specific questions to ask the user for missing info
- extracted_successfully: true only if blood_group AND hospital_area are both present
- bot_reply: a warm, concise reply to show in the chat UI (in English, even if input was Urdu)

Always respond with valid JSON matching the schema exactly."""

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "blood_group": {"type": ["string", "null"]},
        "units_needed": {"type": ["integer", "null"]},
        "hospital_name": {"type": ["string", "null"]},
        "hospital_area": {"type": ["string", "null"]},
        "urgency_level": {"type": "string", "enum": ["critical", "high", "medium", "low"]},
        "patient_name": {"type": ["string", "null"]},
        "needs_clarification": {"type": "boolean"},
        "clarification_questions": {"type": "array", "items": {"type": "string"}},
        "extracted_successfully": {"type": "boolean"},
        "bot_reply": {"type": "string"},
    },
    "required": [
        "blood_group", "units_needed", "hospital_name", "hospital_area",
        "urgency_level", "patient_name", "needs_clarification",
        "clarification_questions", "extracted_successfully", "bot_reply",
    ],
}


async def extract_blood_request(
    message: str,
    conversation_history: list[dict] | None = None,
) -> BloodRequestExtraction:
    """
    Extract structured blood request info from a natural language message.
    conversation_history: list of {"role": "user"/"assistant", "content": str}
    """
    client = get_client()

    messages: list[dict] = []
    if conversation_history:
        messages.extend(conversation_history)
    messages.append({"role": "user", "content": message})

    response = await client.messages.create(
        model=MODEL,
        max_tokens=1024,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=messages,
        output_config={
            "format": {
                "type": "json_schema",
                "name": "blood_request_extraction",
                "schema": RESPONSE_SCHEMA,
                "strict": True,
            }
        },
    )

    # Extract text content from response
    text_content = next(
        (block.text for block in response.content if hasattr(block, "text")),
        "{}",
    )
    data = json.loads(text_content)
    return BloodRequestExtraction(**data)
