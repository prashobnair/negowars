# schemas.py
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator
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

class OfferMessage(BaseMessage):
    type: str = "offer"
    data: "OfferPayload" # Nested validation

class OfferPayload(BaseModel):
    salary: int = Field(..., ge=0, le=1000000)
    bonus: int = Field(..., ge=0, le=10000)
    remote_days: int = Field(..., ge=0, le=5)

class AcceptMessage(BaseMessage):
    type: str = "accept"

class GameOverMessage(BaseMessage):
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

class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)

    @validator("password")
    def password_strength(cls, v):
        # Add more robust password strength checks here, if desired.
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one number")
        if not any(char.isupper() for char in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char.islower() for char in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(char in "!@#$%^&*()_+=-`~[]\{}|;':\",./<>?" for char in v):
            raise ValueError("Password must contain at least one special character")

        return v

class UserResponse(BaseModel): #For the /users/me endpoint
    id: int
    username: str
    email: str
    last_seen: datetime
    class Config:
        from_attributes = True