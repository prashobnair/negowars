# main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uuid
import random
import math
import logging
import asyncio
from chat_evaluator import evaluate_chat
from datetime import datetime

from models import Room, ClientInfo
from config import SCORING_CONFIG
from utils import validate_offer

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

connected_clients = []  # Not directly used, but kept for potential future use
player_counter = 1  # Not directly used anymore, but kept for potential future use.
rooms = {}
next_room_id = 1
max_players_per_room = 2

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

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global next_room_id
    await websocket.accept()
    logger.info(f"Client connected: {websocket.client}")

    room = None
    current_client = None

    try:
        # Find a room to join, or create a new one
        room_id = None
        for room_id, existing_room in rooms.items():
            if len(existing_room.players) < max_players_per_room and not existing_room.game_started:
                room = existing_room
                break  # Exit the loop once a room is found
        else:  # This 'else' belongs to the 'for', and runs if no room was found
            room_id = next_room_id
            room = Room()
            rooms[room_id] = room
            next_room_id += 1

        # Add the player to the room
        player_number = room.next_player_number
        room.next_player_number += 1
        role = "candidate" if player_number % 2 != 0 else "hr"
        bonus_objectives = SCORING_CONFIG[role]["bonus_objectives"]
        bonus_objective_id = random.choice(list(bonus_objectives.keys()))

        client_info = ClientInfo(
            websocket=websocket,
            player=player_number,
            role=role,
            room_id=room_id,
            is_active=True,
            bonus_objective=bonus_objective_id
        )
        room.players.append(client_info)
        current_client = client_info
        logger.info(f"Client added to room {room_id}, Player {player_number}, Role: {role}")

        # Send initial messages and handle waiting/connection status
        await websocket.send_text(f"init|{player_number}|{room_id}")
        await websocket.send_text(f"role|{role}")

        if len(room.players) == 1:
            await websocket.send_text("waiting|Waiting for another player to join...")
            await websocket.send_text("chat_disabled|Chat is disabled until the second player joins.") # send message
        elif len(room.players) == 2:
            # Notify both players that the game can start
            for client in room.players:
                if client.is_active:
                    await client.websocket.send_text("player_connected|A second player has connected. You can start the negotiation now.")
                    await client.websocket.send_text("start_timer|Timer is starting now.")
            room.game_started = True  # Mark the game as started

        # Main message loop
        while True:
            try:
                data = await websocket.receive_text()

                if not current_client or not current_client.is_active:
                    logger.warning(f"Received message from inactive client: {websocket.client}")
                    continue

                # Handle offer messages with validation
                if data.startswith("offer:"):
                    try:
                        _, offer_data = data.split(":", 1)
                        salary_str, bonus_str, remote_days_str = offer_data.split(",")

                        if not all([salary_str.strip(), bonus_str.strip(), remote_days_str.strip()]):
                            await websocket.send_text("error|Invalid offer format")
                            continue

                        try:
                            salary = int(salary_str)
                            bonus = int(bonus_str)
                            remote_days = int(remote_days_str)
                        except ValueError:
                            await websocket.send_text("error|Offer values must be numbers")
                            continue

                        is_valid, error_message = validate_offer(salary, bonus, remote_days)
                        if not is_valid:
                            await websocket.send_text(f"error|{error_message}")
                            continue

                        room.offer = {
                            "salary": salary,
                            "bonus": bonus,
                            "remote_days": remote_days
                        }

                        message_id = str(uuid.uuid4())
                        for client in room.players:
                            if client.is_active:
                                await client.websocket.send_text(
                                    f"offer|{message_id}|{current_client.player}|"
                                    f"salary:{salary},bonus:{bonus},remote_days:{remote_days}"
                                )

                    except Exception as e:
                        logger.error(f"Error processing offer: {e}")
                        await websocket.send_text("error|Invalid offer format")
                        continue

                # --- Handle Typing Status Updates --- (Corrected Placement)
                elif data.startswith("typing:"):
                    _, is_typing_str = data.split(":", 1)
                    for client in room.players:
                        if client.websocket != websocket and client.is_active:
                            try:
                                await client.websocket.send_text(f"typing|{is_typing_str}")  # Corrected format
                            except Exception as e:
                                logger.error(f"Error sending typing status: {e}")
                                client.is_active = False

                # Handle accept message
                elif data == "accept":
                    message_id = str(uuid.uuid4())
                    logger.info(f"Received 'accept' message. Message ID: {message_id}")
                    candidate_client = next((c for c in room.players if c.role == "candidate"), None)
                    hr_client = next((c for c in room.players if c.role == "hr"), None)
                    logger.info(f"Candidate client: {candidate_client}")
                    logger.info(f"HR client: {hr_client}")

                    candidate_score, hr_score = 0, 0
                    final_candidate_score, final_hr_score = 0, 0
                    candidate_chat_bonus, hr_chat_bonus = 0, 0

                    if candidate_client and hr_client:
                        logger.info("Both candidate and HR clients found.")
                        if room.offer["salary"] is not None:
                            logger.info("Calculating scores...")
                            try:
                                candidate_score = calculate_dynamic_candidate_score(
                                    room.offer["salary"], room.offer["bonus"], room.offer["remote_days"],
                                    candidate_client.bonus_objective, True, SCORING_CONFIG["candidate"]
                                )
                                logger.info(f"Candidate score calculated: {candidate_score}")
                                hr_score = calculate_dynamic_hr_score(
                                    room.offer["salary"], room.offer["bonus"], room.offer["remote_days"],
                                    room.offer["salary"] + room.offer["bonus"], hr_client.bonus_objective,
                                    True, SCORING_CONFIG["hr"]
                                )
                                logger.info(f"HR score calculated: {hr_score}")
                                candidate_chat_bonus = evaluate_chat(room.chat_log, candidate_client.player)  # type: ignore
                                hr_chat_bonus = evaluate_chat(room.chat_log, hr_client.player)  # type: ignore
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
                    for client in room.players:
                        if client.is_active:
                            await client.websocket.send_text(gameover_message)

                    for client in room.players:
                        client.is_active = False

                # Handle regular chat messages
                else:
                    message_id = str(uuid.uuid4())
                    try:
                        room.chat_log.append({
                            "sender": current_client.player,
                            "text": data,
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    except Exception as e:
                        logger.error(f"Error adding message to chat log: {e}")

                    for client in room.players:
                        if client.is_active:
                            try:
                                if client.websocket != websocket:
                                    await client.websocket.send_text(f"msg|{message_id}|{current_client.player}|{data}")
                                else:
                                    await client.websocket.send_text(f"ack|{message_id}|{current_client.player}|{data}")
                            except Exception as e:
                                logger.error(f"Error broadcasting message: {e}")
                                client.is_active = False # type: ignore

            except WebSocketDisconnect:
                break  # Exit the inner loop if the client disconnects
            except Exception as e:
                logger.error(f"Error in message loop: {e}")
                break # Exit the loop on other exceptions within the loop
    
    except Exception as e:
        logger.error(f"Error in websocket endpoint outside main loop: {e}")

    finally:
        try:
            if room and current_client:
                current_client.is_active = False
                if current_client in room.players:
                    room.players.remove(current_client)
                if room_id in rooms and not room.players:
                    logger.info(f"Removing empty room {room_id}")
                    del rooms[room_id]
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")