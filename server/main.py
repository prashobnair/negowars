# main.py (Corrected for Guest User Handling - Part 1)
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, status, Depends
from fastapi.middleware.cors import CORSMiddleware
import uuid
import random
import math
import logging
import asyncio
from server.chat_evaluator import evaluate_chat
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from sqlalchemy.ext.asyncio import AsyncSession
from server.models import Room, ClientInfo, User, Session, room_participants
from server.config import settings
from server.config.constants import SCORING_CONFIG, VALIDATION_RANGES
from server.utils import validate_offer
from server import auth
from server.database import get_db, engine, Base, async_session
from server.room_manager import (
    join_or_reconnect,
    handle_disconnect,
    get_room,
    find_available_guest_room # Import find_available_guest_room
)
from fastapi import Depends, HTTPException
from jose import JWTError, jwt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS configuration
origins = [
    "http://localhost:3000",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)

connected_clients = []  # Keep track of connected WebSocket clients.


# --- Temporary Test User Creation (REMOVE BEFORE PRODUCTION) ---
@app.post("/create_test_user")
async def create_test_user(db: AsyncSession = Depends(get_db)):
    # Check for existing user first, to avoid duplicates on reload
    result = await db.execute(select(User).where(User.username == "testuser"))
    existing_user = result.scalars().first()
    if existing_user:
         return {"message": "Test user already exists"}

    hashed_password = auth.get_password_hash("testpassword")
    new_user = User(username="testuser", email="test@example.com", password_hash=hashed_password, is_guest=False)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return {"message": "Test user created"}
# --- END Temporary Test User Creation ---

async def cleanup_inactive_rooms():
    while True:
        await asyncio.sleep(300)  # Check every 5 minutes (300 seconds)
        logger.info("Running room cleanup task...")
        try:
             async with async_session() as db_session:
                # Fetch rooms that are not 'completed'
                result = await db_session.execute(select(Room).where(Room.status != 'completed'))
                all_rooms = result.scalars().all()
                for room in all_rooms:
                    # Check if there are any active clients associated with the room
                    active_clients = [client for client in connected_clients if client.room_id == room.id and client.is_active]
                    if not active_clients:
                        logger.info(f"Cleaning up empty room {room.id}")
                        await db_session.delete(room)
                        await db_session.commit()

        except Exception as e:
            logger.error(f"Error during room cleanup: {e}")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(cleanup_inactive_rooms())


def linear_score(value, min_val, max_val, score_min, score_max):
    if value <= min_val: return score_min
    if value >= max_val: return score_max
    fraction = (value - min_val) / (max_val - min_val)
    return score_min + fraction * (score_max - score_min)

def calculate_dynamic_candidate_score(salary, bonus, remote_days, bonus_objective_id, success, config):
    score = 0
    salary, bonus, remote_days = (x or 0 for x in (salary, bonus, remote_days))
    if salary == 0 and bonus == 0 and remote_days == 0 and not success:
        return config["outcome"]["failure"]
    salary_config = config["base_salary"]
    if salary < salary_config[0]["min"]: salary_score = 0
    elif salary <= salary_config[0]["max"]: salary_score = linear_score(salary, salary_config[0]["min"], salary_config[0]["max"], salary_config[0]["score_min"], salary_config[0]["score_max"])
    else:
        extra = salary_config[1]["points_per_unit"] * math.floor((salary - salary_config[1]["min"]) / salary_config[1]["unit"])
        extra = min(extra, salary_config[1]["max_extra"])
        salary_score = salary_config[1]["base"] + extra
    score += salary_score
    bonus_config = config["sign_on_bonus"]
    if bonus < bonus_config[0]["min"]: bonus_score = 0
    elif bonus <= bonus_config[0]["max"]: bonus_score = linear_score(bonus, bonus_config[0]["min"], bonus_config[0]["max"], bonus_config[0]["score_min"], bonus_config[0]["score_max"])
    else:
        extra = bonus_config[1]["points_per_unit"] * math.floor((bonus - bonus_config[1]["min"]) / bonus_config[1]["unit"])
        extra = min(extra, bonus_config[1]["max_extra"])
        bonus_score = bonus_config[1]["base"] + extra
    score += bonus_score
    remote_days_config = config["remote_days"]
    remote_score = next((item["points"] for item in remote_days_config if item["value"] <= remote_days), 0)
    score += remote_score
    score += config["outcome"]["success"] if success else config["outcome"]["failure"]
    bonus_obj = config["bonus_objectives"].get(bonus_objective_id)
    if bonus_obj:
        if "metric" in bonus_obj and bonus_obj["metric"] == "sign_on_bonus" and bonus >= bonus_obj["threshold"]:
            score += bonus_obj["bonus"]
    return score

def calculate_dynamic_hr_score(salary, bonus, remote_days, total_compensation, bonus_objective_id, success, config):
    score = 0
    salary, bonus, remote_days, total_compensation = (x or 0 for x in (salary, bonus, remote_days, total_compensation))
    if salary == 0 and bonus == 0 and remote_days == 0 and not success:
        return config["outcome"]["failure"]
    salary_config = config["base_salary"]
    if salary <= salary_config[0]["max"]: salary_score = salary_config[0]["score"]
    elif salary <= salary_config[1]["max"]: salary_score = linear_score(salary, salary_config[1]["min"], salary_config[1]["max"], salary_config[1]["score_min"], salary_config[1]["score_max"])
    else:
        penalty = salary_config[2]["penalty_per_unit"] * math.floor((salary - salary_config[2]["min"]) / salary_config[2]["unit"])
        salary_score = max(salary_config[2]["base"] - penalty, salary_config[2]["min_score"])
    score += salary_score
    bonus_config = config["sign_on_bonus"]
    if bonus <= bonus_config[0]["max"]: bonus_score = bonus_config[0]["score"]
    elif bonus <= bonus_config[1]["max"]: bonus_score = linear_score(bonus, bonus_config[1]["min"], bonus_config[1]["max"], bonus_config[1]["score_min"], bonus_config[1]["score_max"])
    else:
        penalty = bonus_config[2]["penalty_per_unit"] * math.floor((bonus - bonus_config[2]["min"]) / bonus_config[2]["unit"])
        bonus_score = max(bonus_config[2]["base"] - penalty, bonus_config[2]["min_score"])
    score += bonus_score
    total_comp_config = config["total_compensation"]
    comp_score = (total_comp_config[0]["score"] if total_compensation <= total_comp_config[0]["max"] else
                  linear_score(total_compensation, total_comp_config[1]["min"], total_comp_config[1]["max"], total_comp_config[1]["score_min"], total_comp_config[1]["score_max"]) if total_compensation <= total_comp_config[1]["max"] else
                  total_comp_config[2]["score"])
    score += comp_score
    remote_days_config = config["remote_days"]
    remote_score = next((item["points"] for item in remote_days_config if item["value"] == remote_days), 0)
    score += remote_score
    score += config["outcome"]["success"] if success else config["outcome"]["failure"]
    bonus_obj = config["bonus_objectives"].get(bonus_objective_id)
    if bonus_obj and "metric" in bonus_obj and bonus_obj["metric"] == "total_compensation" and total_compensation <= bonus_obj["threshold"]:
        score += bonus_obj["bonus"]
    return score

async def authenticate_websocket(token: str, db: AsyncSession) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    if token == "guest":
        # Create a temporary guest user *without* saving to the database
        guest_user = User(id=-1, username="Guest", email="", password_hash="", is_guest=True)  # Dummy ID
        return guest_user

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        session_id: str = payload.get("sub")
        if session_id is None:
            raise credentials_exception
        result = await db.execute(select(Session).where(Session.id == session_id))
        session = result.scalars().first()
        if session is None or session.expires_at < datetime.now(timezone.utc):
            raise credentials_exception
        result = await db.execute(select(User).where(User.id == session.user_id))
        user = result.scalars().first()
        if user is None:
            raise credentials_exception
        return user
    except JWTError:
        raise credentials_exception

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...), db: AsyncSession = Depends(get_db)):
    logger.info(f"Initial session ID: {id(db)}")
    try:
        user = await authenticate_websocket(token, db)
    except HTTPException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    logger.info(f"Client connected: {websocket.client}, User ID: {user.id}")

    current_client = None

    try:
        async with db:
            logger.info(f"Entered async session context with ID: {id(db)}")
            logger.info(f"Session transaction status: {'open' if db.in_transaction() else 'closed'}")

            # --- Pass connected_clients here ---
            room = await join_or_reconnect(db, user, connected_clients)
            logger.info(f"After join_or_reconnect - Session active: {db.is_active}")

            room_id = room.id
            player_number = len(room.participants) +1

            logger.info(f"Pre-role query session status: {db.is_active}")

            if user.is_guest:
                participant_count = sum(1 for client in connected_clients if client.room_id == room_id and client.is_active)
                role = "candidate" if participant_count % 2 == 0 else "hr"
                logger.info(f"Guest user: Role determined as {role}")
            else:
                result = await db.execute(
                    select(room_participants.c.role)
                    .where(room_participants.c.user_id == user.id)
                    .where(room_participants.c.room_id == room.id)
                )
                logger.info(f"Result type: {type(result)}")
                row = result.first()
                logger.info(f"Row type: {type(row)}")
                role = row[0] if row else None
                logger.info(f"Registered user: Role from DB: {role}")

                if not role:
                    logger.error("Error getting user role")
                    await websocket.close(code=1011)
                    return

            bonus_objectives = SCORING_CONFIG[role]["bonus_objectives"]
            bonus_objective_id = random.choice(list(bonus_objectives.keys()))

            client_info = ClientInfo(
                websocket=websocket,
                player=user.id if not user.is_guest else -1,
                role=role,
                room_id=room_id,
                is_active=True,
                bonus_objective=bonus_objective_id
            )
            current_client = client_info
            connected_clients.append(current_client)

            logger.info(f"User {user.id} (Player {player_number}, Role: {role}) joined/reconnected to room {room_id}")

            await websocket.send_text(f"init|{player_number}|{room_id}")
            await websocket.send_text(f"role|{role}{' (Guest)' if user.is_guest else ''}")

            if len(room.participants) == 1:
                await websocket.send_text("waiting|Waiting for another player to join...")
                await websocket.send_text("chat_disabled|Chat is disabled until the second player joins.")
            elif len(room.participants) > 1:
                for other_client in connected_clients:
                    if other_client.room_id == room_id and other_client.is_active:
                        await other_client.websocket.send_text(
                            "player_connected|A second player has connected. You can start the negotiation now.")
                        await other_client.websocket.send_text("start_timer|Timer is starting now.")

                room.status = 'active'
                await db.commit()

            # --- Main Message Loop ---
            while True:
                try:
                    data = await websocket.receive_text()

                    if data.startswith("offer:"):
                        # --- Handle Offer Messages ---
                        try:
                            _, offer_data = data.split(":", 1)
                            salary_str, bonus_str, remote_days_str = offer_data.split(",")

                            if not all([salary_str.strip(), bonus_str.strip(), remote_days_str.strip()]):
                              await websocket.send_text("error|Invalid offer format")
                              continue

                            salary = int(salary_str)
                            bonus = int(bonus_str)
                            remote_days = int(remote_days_str)

                            # Validate
                            is_valid, error_message = validate_offer(salary, bonus, remote_days)
                            if not is_valid:
                                await websocket.send_text(f"error|{error_message}")
                                continue

                            # Store the offer in the room's game_state (using a dictionary)
                            async with async_session() as db_session:
                                result = await db_session.execute(select(Room).where(Room.id == room_id).options(joinedload(Room.participants)))
                                room = result.scalars().first()
                                if room:
                                    if room.game_state is None:
                                       room.game_state = {}
                                    room.game_state['offer'] = {
                                        "salary": salary,
                                        "bonus": bonus,
                                        "remote_days": remote_days,
                                        "lastSender": current_client.player,
                                    }
                                    await db_session.commit()
                                    logger.info(f"Offer saved for room {room_id}: {room.game_state['offer']}")
                                else:
                                   logger.warning("Room Not Found")

                            message_id = str(uuid.uuid4())
                            for client in connected_clients:
                                if client.room_id == room_id and client.is_active and client.websocket != websocket:
                                    await client.websocket.send_text(f"offer|{message_id}|{current_client.player}|salary:{salary},bonus:{bonus},remote_days:{remote_days}")
                        except (ValueError, IndexError) as e:
                            logger.error(f"Invalid offer format: {e}")
                            continue

                    elif data.startswith("typing:"):
                        # --- Handle Typing Status Updates ---
                        _, is_typing_str = data.split(":", 1)
                        for client in connected_clients:
                            if client.room_id == room_id and client.is_active and client.websocket != websocket:
                                try:
                                    await client.websocket.send_text(f"typing|{is_typing_str}")
                                except Exception as e:
                                    logger.error(f"Error sending typing status: {e}")

                    elif data == "accept":
                        # --- Handle "accept" Message ---
                        message_id = str(uuid.uuid4())
                        logger.info(f"Received 'accept' message. Message ID: {message_id}")

                        async with async_session() as db_session:
                            result = await db_session.execute(select(Room).where(Room.id == room_id).options(joinedload(Room.participants)))
                            room = result.scalars().first()
                            if not room:
                                logger.error(f"Room {room_id} not found during accept.")
                                continue

                            # Find the candidate and HR clients *within the room* using connected_clients and roles
                            candidate_client = next((c for c in connected_clients if c.room_id == room_id and c.role == "candidate" and c.is_active), None)
                            hr_client = next((c for c in connected_clients if c.room_id == room_id and c.role == "hr" and c.is_active), None)


                            candidate_score = 0
                            hr_score = 0
                            final_candidate_score = 0
                            final_hr_score = 0
                            candidate_chat_bonus = 0
                            hr_chat_bonus = 0

                            if candidate_client and hr_client:
                                logger.info("Both candidate and HR clients found.")

                                if room.game_state and room.game_state.get('offer', {}).get('salary') is not None:
                                    logger.info("Calculating scores...")
                                    try:
                                       # Get User IDs for registered players.  Use -1 for guests.
                                        candidate_user_id = candidate_client.player
                                        hr_user_id = hr_client.player

                                        # Find the participants and get bonus objective, handling guests correctly
                                        if candidate_user_id != -1:  # Registered candidate
                                            candidate_participant_result = await db_session.execute(select(room_participants).where(room_participants.c.user_id == candidate_user_id).where(room_participants.c.room_id == room.id))
                                            candidate_participant = candidate_participant_result.scalars().first()
                                        else:  # Guest candidate - use role directly from ClientInfo
                                            candidate_participant = candidate_client

                                        if hr_user_id != -1:  # Registered HR
                                            hr_participant_result = await db_session.execute(select(room_participants).where(room_participants.c.user_id == hr_user_id).where(room_participants.c.room_id == room.id))
                                            hr_participant = hr_participant_result.scalars().first()
                                        else: # Guest HR
                                            hr_participant = hr_client

                                        if candidate_participant is None or hr_participant is None:
                                            logger.warning("One of the participants not found")
                                            continue


                                        candidate_score = calculate_dynamic_candidate_score(
                                            room.game_state['offer']['salary'],
                                            room.game_state['offer']['bonus'],
                                            room.game_state['offer']['remote_days'],
                                            candidate_participant.bonus_objective,
                                            True,
                                            SCORING_CONFIG["candidate"]
                                        )
                                        logger.info(f"Candidate score calculated: {candidate_score}")

                                        hr_score = calculate_dynamic_hr_score(
                                            room.game_state['offer']['salary'],
                                            room.game_state['offer']['bonus'],
                                            room.game_state['offer']['remote_days'],
                                            room.game_state['offer']['salary'] + room.game_state['offer']['bonus'],
                                            hr_participant.bonus_objective,
                                            True,
                                            SCORING_CONFIG["hr"]
                                        )
                                        logger.info(f"HR score calculated: {hr_score}")

                                        # --- Compute Chat Bonus ---
                                        logger.info(f"Computing chat quality bonus")
                                        loop = asyncio.get_running_loop()
                                        candidate_chat_bonus = await loop.run_in_executor(None, evaluate_chat, room.chat_log, candidate_client.player)
                                        hr_chat_bonus = await loop.run_in_executor(None, evaluate_chat, room.chat_log, hr_client.player)


                                        final_candidate_score = candidate_score + candidate_chat_bonus
                                        final_hr_score = hr_score + hr_chat_bonus
                                    except Exception as e:
                                        logger.exception(f"Error during score calculation: {e}")
                                else:
                                    logger.info("No offer made yet, skipping score calculation.")

                            else:
                                logger.warning("Either candidate or HR client not found in the room.")

                            gameover_message = (
                                f"gameover|{message_id}|Negotiation successful!|{final_candidate_score}|{final_hr_score}|"
                                f"{candidate_client.bonus_objective if candidate_client else 'N/A'}|"
                                f"{hr_client.bonus_objective if hr_client else 'N/A'}"
                            )

                            # Mark the room as completed
                            room.status = 'completed'
                            await db_session.commit()

                            for client in connected_clients:
                                if client.room_id == room_id and client.is_active:
                                    await client.websocket.send_text(gameover_message)
                    elif data.startswith("gameover|timeout"):
                        # --- Handle Timeout ---
                        message_id = str(uuid.uuid4())
                        async with async_session() as db_session:
                            result = await db_session.execute(select(Room).where(Room.id == room_id).options(joinedload(Room.participants)))
                            room = result.scalars().first()
                           # Find the candidate and HR clients *within the room* using connected_clients and roles
                            candidate_client = next((c for c in connected_clients if c.room_id == room_id and c.role == "candidate" and c.is_active), None)
                            hr_client = next((c for c in connected_clients if c.room_id == room_id and c.role == "hr" and c.is_active), None)


                            candidate_score = 0
                            hr_score = 0

                            if candidate_client and hr_client:
                                candidate_score = calculate_dynamic_candidate_score(
                                    0, 0, 0, "", False, SCORING_CONFIG["candidate"]
                                )
                                hr_score = calculate_dynamic_hr_score(
                                    0, 0, 0, 0, "", False, SCORING_CONFIG["hr"]
                                )

                                logger.info(f"Computing chat quality bonus")
                                loop = asyncio.get_running_loop()
                                candidate_chat_bonus = await loop.run_in_executor(None, evaluate_chat, room.chat_log, candidate_client.player)
                                hr_chat_bonus = await loop.run_in_executor(None, evaluate_chat, room.chat_log, hr_client.player)

                                final_candidate_score = candidate_score + candidate_chat_bonus
                                final_hr_score = hr_score + hr_chat_bonus
                            else:
                                final_candidate_score = 0
                                final_hr_score = 0

                            gameover_message = f"gameover|{message_id}|Negotiation timed out!|{final_candidate_score}|{final_hr_score}|{candidate_client.bonus_objective if candidate_client else 'N/A'}|{hr_client.bonus_objective if hr_client else 'N/A'}"

                            for client in connected_clients:
                                if client.is_active:
                                    await client.websocket.send_text(gameover_message)
                            for client in connected_clients: #Closing client connection
                                if client.room_id == room_id:
                                    client.is_active = False

                    else:
                        # --- Handle Regular Chat Messages ---
                        message_id = str(uuid.uuid4())
                        # Log the message in the room's chat log (inside game_state).
                        async with async_session() as db_session:
                            result = await db_session.execute(select(Room).where(Room.id == room_id))
                            room = result.scalars().first()
                            if room:
                                if room.game_state is None:  # Initialize game_state if it's None
                                    room.game_state = {}
                                if 'chat_log' not in room.game_state: # Use in operator
                                    room.game_state['chat_log'] = []
                                room.game_state['chat_log'].append({  # Access chat_log within game_state
                                    "sender": current_client.player,
                                    "text": data,
                                    "timestamp": datetime.utcnow().isoformat()
                                })
                                await db_session.commit()

                        # Broadcast to all players in the *room*
                        for client in connected_clients:
                            if client.room_id == room_id and client.is_active:  # Check room_id and active
                                if client.websocket != websocket:
                                    await client.websocket.send_text(f"msg|{message_id}|{current_client.player}|{data}")
                                else:
                                    await client.websocket.send_text(f"ack|{message_id}|{current_client.player}|{data}")
                except WebSocketDisconnect:
                    logger.info(f"Client disconnected from room: {room_id}")
                    break
                except Exception as e:
                    logger.error(f"Error in message loop: {e}")
                    break

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if current_client:
            current_client.is_active = False
            if current_client in connected_clients:
                connected_clients.remove(current_client)