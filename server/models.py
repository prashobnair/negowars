# models.py (Corrected to use JSONB)
from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey, Table, Boolean  # Keep JSON import
from sqlalchemy.dialects.postgresql import JSONB  # Import JSONB
from sqlalchemy.orm import relationship
from server.database import Base
from datetime import datetime, timezone
import uuid
from pydantic import BaseModel, ConfigDict, Field
from fastapi import WebSocket

# Association table, with cascading deletes on BOTH foreign keys
room_participants = Table('room_participants', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete="CASCADE"), primary_key=True),
    Column('room_id', Integer, ForeignKey('rooms.id', ondelete="CASCADE"), primary_key=True),
    Column('role', String(20))  # 'candidate' or 'hr'
)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    last_seen = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    is_guest = Column(Boolean, default=False)
    rooms = relationship("Room", secondary=room_participants, back_populates="participants")
    sessions = relationship('Session', backref='user')


class Session(Base):
    __tablename__ = 'sessions'
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    # Add any other session data you need (e.g., user agent, IP address)


class Room(Base):
    __tablename__ = 'rooms'
    id = Column(Integer, primary_key=True)
    status = Column(String(20), default='waiting')  # 'waiting', 'active', 'completed'
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    game_state = Column(JSONB)  # Changed to JSONB
    participants = relationship("User", secondary=room_participants, back_populates="rooms")


class ClientInfo(BaseModel):
    websocket: WebSocket
    player: int
    role: str
    room_id: int
    is_active: bool
    bonus_objective: str

    model_config = ConfigDict(arbitrary_types_allowed=True)