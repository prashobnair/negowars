from pydantic import BaseModel, PositiveInt
from fastapi import WebSocket
from typing import Optional, List, Dict, Any

class ClientInfo(BaseModel):
    websocket: WebSocket
    player: int
    role: str
    room_id: PositiveInt
    is_active: bool
    bonus_objective: str

    class Config:
        arbitrary_types_allowed = True

class Room(BaseModel):
    players: List[ClientInfo] = []
    game_started: bool = False
    next_player_number: int = 1
    offer: Dict[str, Optional[int]] = {"salary": None, "bonus": None, "remote_days": None}
    chat_log: List[Dict[str, Any]] = []
    
    class Config:
        arbitrary_types_allowed = True