# schemas.py -  This should be the SAME as the previous response's schemas.py:
from pydantic import BaseModel, conint, constr, validator, Field
from typing import Optional

class BaseMessage(BaseModel):
    type: str

class ChatMessage(BaseMessage):
    type: str = "msg"  # Enforce the type
    sender: int
    text: str

    @validator("text")
    def text_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Chat message cannot be empty")
        return v
class AckMessage(BaseMessage):
    type: str = "ack"
    messageId: str
    playerNumber: int
    messageContent: str

class TypingMessage(BaseMessage):
    type: str = "typing"
    isTyping: bool

class OfferMessage(BaseMessage):  # Renamed from just OfferPayload
    type: str = "offer"
    data: "OfferPayload" # Nested validation

class OfferPayload(BaseModel): # Keep this separate for reusability
    salary: int = Field(..., ge=0, le=1000000)
    bonus: int = Field(..., ge=0, le=10000)
    remote_days: int = Field(..., ge=0, le=5)

class AcceptMessage(BaseMessage):
    type: str = "accept"

class GameOverMessage(BaseMessage): # For sending game over info
    type: str = "gameover"
    messageId: str
    outcome: str
    candidateScore: int
    hrScore: int
    candidateBonus: str
    hrBonus: str
    reason: Optional[str] = None # Optional reason (e.g., "timeout")

class ErrorMessage(BaseMessage):
    type: str = "error"
    message: str