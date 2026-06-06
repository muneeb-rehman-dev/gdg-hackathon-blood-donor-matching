from pydantic import BaseModel
from typing import Optional, Literal


class ChatMessage(BaseModel):
    session_id: str
    message: str
    role: Literal["user", "assistant"] = "user"


class ChatResponse(BaseModel):
    session_id: str
    bot_reply: str
    request_id: Optional[str] = None
    needs_clarification: bool = False
    clarification_questions: list[str] = []
    status: Literal["extracting", "matching", "outreach_started", "clarification_needed", "error"] = "extracting"
