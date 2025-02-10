from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uuid
import random
import math
import logging
import asyncio

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

connected_clients = []  # List to store client info (websocket and player number)
player_counter = 1  # Counter to assign player numbers

# Add these constants at the top of the file
SALARY_MIN = 0
SALARY_MAX = 1000000
BONUS_MIN = 0
BONUS_MAX = 10000
REMOTE_DAYS_MIN = 0
REMOTE_DAYS_MAX = 5

# --- Room Management ---
rooms = {}  # Dictionary to store rooms: {room_id: {room_data}}
next_room_id = 1
max_players_per_room = 2  # Set the maximum number of players per room


# ---------- Scoring Configurations (Hardcoded for MVP) ----------
# Candidate scoring configuration (can be customized per game)
candidate_scoring_config = {
    "base_salary": [
        # Range from $65k to $75k: linear interpolation from 20 to 60 points.
        {"min": 65000, "max": 75000, "score_min": 20, "score_max": 60},
        # Above $75k: start at 60, add 2 points per extra $1,000, capped at an extra 20 points.
        {"min": 75000, "max": None, "points_per_unit": 2, "unit": 1000, "max_extra": 20, "base": 60}
    ],
    "sign_on_bonus": [
        # Range from $5k to $8k: linear interpolation from 20 to 40 points.
        {"min": 5000, "max": 8000, "score_min": 20, "score_max": 40},
        # Above $8k: add 5 points per extra $500, capped at an extra 20 points.
        {"min": 8000, "max": None, "points_per_unit": 5, "unit": 500, "max_extra": 20, "base": 40}
    ],
    "remote_days": [
        # For remote work days, we simply define fixed points.
        # Less than 2 days: 0 points; exactly 2 days: 10; 3 or more: 20.
        {"value": 2, "points": 10},
        {"value": 3, "points": 20}  # Use this if remote_days >= 3.
    ],
    "outcome": {
        "success": 50,
        "failure": -50
    },
    "bonus_objectives": {
        # Bonus objectives are keyed by an id. They may refer to a specific metric.
        "debt": {"metric": "sign_on_bonus", "threshold": 7000, "bonus": 30},
    }
}

# HR scoring configuration (can be customized per game)
hr_scoring_config = {
    "base_salary": [
        # Salary <= $65k: 30 points.
        {"min": None, "max": 65000, "score": 30},
        # From $65k to $70k: linear decrease from 30 to 20.
        {"min": 65000, "max": 70000, "score_min": 30, "score_max": 20},
        # Above $70k: subtract 5 points per extra $1k from $70k, floor at -20.
        {"min": 70000, "max": None, "penalty_per_unit": 5, "unit": 1000, "base": 20, "min_score": -20}
    ],
    "sign_on_bonus": [
        # Bonus <= $5k: 20 points.
        {"min": None, "max": 5000, "score": 20},
        # $5k to $8k: linear decrease from 20 to 10.
        {"min": 5000, "max": 8000, "score_min": 20, "score_max": 10},
        # Above $8k: subtract 5 points per extra $500, floor at -10.
        {"min": 8000, "max": None, "penalty_per_unit": 5, "unit": 500, "base": 10, "min_score": -10}
    ],
    "total_compensation": [
        # Total Compensation <= $80k: 30 points.
        {"min": None, "max": 80000, "score": 30},
        # $80k to $85k: linear decrease from 30 to 10.
        {"min": 80000, "max": 85000, "score_min": 30, "score_max": 10},
        # Above $85k: flat -20.
        {"min": 85000, "max": None, "score": -20}
    ],
    "remote_days": [
        # 0 days: 10 points; 1 day: 5 points; otherwise 0.
        {"value": 0, "points": 10},
        {"value": 1, "points": 5}
    ],
    "outcome": {
        "success": 50,
        "failure": -50
    },
    "bonus_objectives": {
        "budget": {"metric": "total_compensation", "threshold": 76000, "bonus": 30}
    }
}

# ---------- Utility Functions ----------
def linear_score(value, min_val, max_val, score_min, score_max):
    """
    Returns a linearly interpolated score for value between min_val and max_val.
    If value is below min_val, returns score_min.
    If value is above max_val, returns score_max.
    """
    if value <= min_val:
        return score_min
    elif value >= max_val:
        return score_max
    else:
        fraction = (value - min_val) / (max_val - min_val)
        return score_min + fraction * (score_max - score_min)

# ---------- Dynamic Candidate Scoring Function ----------
def calculate_dynamic_candidate_score(salary, bonus, remote_days, bonus_objective_id, success, config): # Add config
    score = 0
    
    salary = salary or 0
    bonus = bonus or 0
    remote_days = remote_days or 0

    # NEW: Check if an offer has been made.  If not, only consider outcome
    if salary == 0 and bonus == 0 and remote_days == 0 and success == False:
        score += config["outcome"]["failure"]  # Only the failure penalty
        return score
    
    # Base Salary Scoring:
    salary_config = config["base_salary"]  # Use the passed-in config
    
    if salary < salary_config[0]["min"]:
        salary_score = 0
    elif salary <= salary_config[0]["max"]:
        salary_score = linear_score(salary, salary_config[0]["min"], salary_config[0]["max"],
                                    salary_config[0]["score_min"], salary_config[0]["score_max"])
    else:
        extra = salary_config[1]["points_per_unit"] * math.floor((salary - salary_config[1]["min"]) / salary_config[1]["unit"])
        extra = min(extra, salary_config[1]["max_extra"])
        salary_score = salary_config[1]["base"] + extra
    score += salary_score
    
    # Sign-On Bonus Scoring:
    bonus_config = config["sign_on_bonus"]  # Use the passed-in config

    if bonus < bonus_config[0]["min"]:
        bonus_score = 0
    elif bonus <= bonus_config[0]["max"]:
        bonus_score = linear_score(bonus, bonus_config[0]["min"], bonus_config[0]["max"],
                                   bonus_config[0]["score_min"], bonus_config[0]["score_max"])
    else:
        extra = bonus_config[1]["points_per_unit"] * math.floor((bonus - bonus_config[1]["min"]) / bonus_config[1]["unit"])
        extra = min(extra, bonus_config[1]["max_extra"])
        bonus_score = bonus_config[1]["base"] + extra
    score += bonus_score
    # Remote Work Days Scoring:
    remote_days_config = config["remote_days"]  # Use the passed-in config
    if remote_days < 2:
      remote_score = 0
    elif remote_days == 2:
      for item in remote_days_config:
        if item["value"] == remote_days:
          remote_score = item["points"]
          break
    else:
      for item in remote_days_config:
        if item["value"] <= remote_days:
          remote_score = item["points"]

    score += remote_score
    # Outcome Modifier:
    score += config["outcome"]["success"] if success else config["outcome"]["failure"]

    # Bonus Objective Bonus:
    bonus_obj = config["bonus_objectives"].get(bonus_objective_id)
    if bonus_obj:
        if "metric" in bonus_obj:
            metric = bonus_obj["metric"]
            if metric == "sign_on_bonus" and bonus >= bonus_obj["threshold"]:
                score += bonus_obj["bonus"]
        else:
            score += bonus_obj["bonus"]

    return score
# ---------- Dynamic HR Scoring Function ----------
def calculate_dynamic_hr_score(salary, bonus, remote_days, total_compensation, bonus_objective_id, success, config): # Add config
    score = 0
    # Handle None values by defaulting to 0
    salary = salary or 0
    bonus = bonus or 0
    remote_days = remote_days or 0
    total_compensation = total_compensation or 0

    # NEW: Check if an offer has been made. If not, only consider outcome
    if salary == 0 and bonus == 0 and remote_days == 0 and success == False:
        score += config["outcome"]["failure"]  # Only the failure penalty
        return score
    
    # Base Salary Scoring:
    salary_config = config["base_salary"]  # Use the passed-in config
    if salary <= salary_config[0]["max"]:
        salary_score = salary_config[0]["score"]
    elif salary <= salary_config[1]["max"]:
        salary_score = linear_score(salary, salary_config[1]["min"], salary_config[1]["max"],
                                    salary_config[1]["score_min"], salary_config[1]["score_max"])
    else:
        penalty = salary_config[2]["penalty_per_unit"] * math.floor((salary - salary_config[2]["min"]) / salary_config[2]["unit"])
        salary_score = max(salary_config[2]["base"] - penalty, salary_config[2]["min_score"])
    score += salary_score

    # Sign-On Bonus Scoring:
    bonus_config = config["sign_on_bonus"]  # Use the passed-in config
    if bonus <= bonus_config[0]["max"]:
        bonus_score = bonus_config[0]["score"]
    elif bonus <= bonus_config[1]["max"]:
        bonus_score = linear_score(bonus, bonus_config[1]["min"], bonus_config[1]["max"],
                                bonus_config[1]["score_min"], bonus_config[1]["score_max"])
    else:
        penalty = bonus_config[2]["penalty_per_unit"] * math.floor((bonus - bonus_config[2]["min"]) / bonus_config[2]["unit"])
        bonus_score = max(bonus_config[2]["base"] - penalty, bonus_config[2]["min_score"])
    score += bonus_score

    # Total Compensation Scoring:
    total_comp_config = config["total_compensation"] # Use the passed-in config
    if total_compensation <= total_comp_config[0]["max"]:
        comp_score = total_comp_config[0]["score"]
    elif total_compensation <= total_comp_config[1]["max"]:
        comp_score = linear_score(total_compensation, total_comp_config[1]["min"], total_comp_config[1]["max"], total_comp_config[1]["score_min"], total_comp_config[1]["score_max"])
    else:
        comp_score = total_comp_config[2]["score"]

    score += comp_score

    # Remote Work Days Scoring:
    remote_days_config = config["remote_days"]  # Use the passed-in config

    if remote_days == remote_days_config[0]["value"]:
        remote_score = remote_days_config[0]["points"]
    elif remote_days == remote_days_config[1]["value"]:
        remote_score = remote_days_config[1]["points"]
    else:
        remote_score = 0
    score += remote_score

    # Outcome Modifier:
    score += config["outcome"]["success"] if success else config["outcome"]["failure"]

    # Bonus Objective Bonus:
    bonus_obj = config["bonus_objectives"].get(bonus_objective_id)
    if bonus_obj:
        if "metric" in bonus_obj:
            metric = bonus_obj["metric"]
            if metric == "total_compensation" and total_compensation <= bonus_obj["threshold"]:
                score += bonus_obj["bonus"]
        else:
            score += bonus_obj["bonus"]

    return score

def validate_offer(salary: int, bonus: int, remote_days: int) -> tuple[bool, str]:
    """
    Validates an offer's values.
    Returns (is_valid: bool, error_message: str)
    """
    try:
        # Validate salary
        if not isinstance(salary, (int, float)) or not float(salary).is_integer():
            return False, "Salary must be a whole number"
        salary = int(salary)
        if salary < SALARY_MIN or salary > SALARY_MAX:
            return False, f"Salary must be between ${SALARY_MIN} and ${SALARY_MAX}"

        # Validate bonus
        if not isinstance(bonus, (int, float)) or not float(bonus).is_integer():
            return False, "Bonus must be a whole number"
        bonus = int(bonus)
        if bonus < BONUS_MIN or bonus > BONUS_MAX:
            return False, f"Bonus must be between ${BONUS_MIN} and ${BONUS_MAX}"

        # Validate remote days
        if not isinstance(remote_days, (int, float)) or not float(remote_days).is_integer():
            return False, "Remote days must be a whole number"
        remote_days = int(remote_days)
        if remote_days < REMOTE_DAYS_MIN or remote_days > REMOTE_DAYS_MAX:
            return False, f"Remote days must be between {REMOTE_DAYS_MIN} and {REMOTE_DAYS_MAX}"

        return True, ""
    except (ValueError, TypeError):
        return False, "Invalid offer values"

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global next_room_id  # Declare next_room_id as global
    logger.info("WebSocket endpoint called")
    await websocket.accept()
    logger.info(f"Client connected: {websocket.client}")

    room = None  # Initialize room variable

    try:
        # Find a room to join, or create a new one
        room_id = None
        for id, room in rooms.items():
            if len(room["players"]) < max_players_per_room and not room["game_started"]:
                room_id = id
                break
        if room_id is None:
            room_id = next_room_id
            rooms[room_id] = {
                "players": [],
                "next_player_number": 1,
                "game_started": False,
                "offer": {"salary": None, "bonus": None, "remote_days": None}
            }
            next_room_id += 1

        room = rooms[room_id]  # Assign room after checking
        player_number = room["next_player_number"]
        room["next_player_number"] += 1
        role = "candidate" if player_number % 2 != 0 else "hr"

        # NEW: Assign a bonus objective based on the role
        bonus_objectives = candidate_scoring_config["bonus_objectives"] if role == "candidate" else hr_scoring_config["bonus_objectives"]
        bonus_objective_id = random.choice(list(bonus_objectives.keys()))  # Randomly select a bonus objective ID

        client_info = {
            "websocket": websocket,
            "player": player_number,
            "role": role,
            "room_id": room_id,
            "is_active": True,
            "bonus_objective": bonus_objective_id  # Add this line to set the bonus objective
        }
        room["players"].append(client_info)
        logger.info(f"Client added to room {room_id}, Player {player_number}, Role: {role}")

        # Send initial messages with error handling
        try:
            await websocket.send_text(f"init|{player_number}|{room_id}")
            await websocket.send_text(f"role|{role}")
        except Exception as e:
            logger.error(f"Error sending initial messages: {e}")
            client_info["is_active"] = False
            if client_info in room["players"]:
                room["players"].remove(client_info)
            return

        # Check if this is the only player in the room
        if len(room["players"]) == 1:
            logger.info(f"Player {client_info['player']} is waiting for another player to join.")
            await websocket.send_text("waiting|Waiting for another player to join...")
            await websocket.send_text("chat_disabled|Chat is disabled until the second player joins.")
        else:
            # Notify both players that the second player has joined
            for player in room["players"]:
                if player["is_active"]:
                    await player["websocket"].send_text("player_connected|A second player has connected. You can start the negotiation now.")
                    # Start the timer when both players are connected
                    await player["websocket"].send_text("start_timer|Timer is starting now.")

        # Main message loop
        while True:
            try:
                data = await websocket.receive_text()
                current_client = next((c for c in room["players"] if c["websocket"] == websocket), None)
                if not current_client or not current_client["is_active"]:
                    logger.warning(f"Received message from inactive client: {websocket.client}. Ignoring.")
                    continue

                logger.info(f"Received from Player {current_client['player']} in Room {current_client['room_id']}: {data}")
                logger.info(f"Current players in room {room_id}: {[c['player'] for c in room['players']]}")

                # Log the number of players before evaluating the condition
                player_count = len(room["players"])
                logger.info(f"Evaluating game start conditions. Current player count: {player_count}")

                # --- Start the game if we have at least two players ---
                if player_count == 2 and not room["game_started"]:
                    room["game_started"] = True
                    logger.info(f"Game started in room {room_id}")
                    for player in room["players"]:
                        if player["is_active"]:
                            await player["websocket"].send_text("game_started|Both players are connected. The game is starting!")
                            # Start the timer when both players are connected
                            await player["websocket"].send_text("start_timer|Timer is starting now.")
                elif player_count < 2:
                    logger.info(f"Player {current_client['player']} is waiting for another player to join.")
                    await websocket.send_text("waiting|Waiting for another player to join...")
                else:
                    logger.info("Unexpected condition: More than 2 players in the room.")

                # --- Handle Offer Messages ---
                if data.startswith("offer:"):
                    _, offer_data = data.split(":", 1)
                    try:
                        salary_str, bonus_str, remote_days_str = offer_data.split(",")
                        if not all([salary_str.strip(), bonus_str.strip(), remote_days_str.strip()]):
                            continue

                        salary = int(salary_str)
                        bonus = int(bonus_str)
                        remote_days = int(remote_days_str)

                        # Update the *room's* offer
                        room["offer"]["salary"] = salary
                        room["offer"]["bonus"] = bonus
                        room["offer"]["remote_days"] = remote_days

                        message_id = str(uuid.uuid4())
                        for client in room["players"]:  # Broadcast to all players in the *room*
                            if client["is_active"]: # Check for active
                                await client["websocket"].send_text(f"offer|{message_id}|{current_client['player']}|salary:{salary},bonus:{bonus},remote_days:{remote_days}")

                    except (ValueError, IndexError) as e:
                        logger.error(f"Invalid offer format: {e}")
                        continue


                # --- Handle "accept" Message ---
                elif data == "accept":
                    message_id = str(uuid.uuid4())
                    logger.info(f"Received 'accept' message. Message ID: {message_id}")

                    # Find the candidate and HR clients *within the room*
                    candidate_client = next((c for c in room["players"] if c["role"] == "candidate"), None)
                    hr_client = next((c for c in room["players"] if c["role"] == "hr"), None)
                    logger.info(f"Candidate client: {candidate_client}")
                    logger.info(f"HR client: {hr_client}")

                    candidate_score = 0
                    hr_score = 0

                    if candidate_client and hr_client:
                        logger.info("Both candidate and HR clients found.")
                        offering_client = candidate_client if current_client["role"] == "hr" else hr_client
                        # Use the *room's* offer for calculations
                        if room["offer"]["salary"] is not None: # Check if offer exists
                            logger.info("Calculating scores...")
                            try:
                                candidate_score = calculate_dynamic_candidate_score(
                                    room["offer"]["salary"],
                                    room["offer"]["bonus"],
                                    room["offer"]["remote_days"],
                                    candidate_client["bonus_objective"],
                                    True,
                                    candidate_scoring_config
                                )
                                logger.info(f"Candidate score calculated: {candidate_score}")

                                hr_score = calculate_dynamic_hr_score(
                                    room["offer"]["salary"],
                                    room["offer"]["bonus"],
                                    room["offer"]["remote_days"],
                                    room["offer"]["salary"] + room["offer"]["bonus"],
                                    hr_client["bonus_objective"],
                                    True,
                                    hr_scoring_config
                                )
                                logger.info(f"HR score calculated: {hr_score}")
                            except Exception as e:
                                logger.exception(f"Error during score calculation: {e}")
                        else:
                            logger.info("No offer made yet, skipping score calculation.")

                    else:
                        logger.warning("Either candidate or HR client not found in the room.")


                    gameover_message = f"gameover|{message_id}|Negotiation successful!|{candidate_score}|{hr_score}|{candidate_client['bonus_objective'] if candidate_client else 'N/A'}|{hr_client['bonus_objective'] if hr_client else 'N/A'}"
                    for client in room["players"]:  # Send to all players in the *room*
                        if client["is_active"]: # Check for active
                            await client["websocket"].send_text(gameover_message)

                    # Instead of clearing the room, mark clients as inactive
                    for client in room["players"]:
                      client["is_active"] = False

                    # Optionally, clean up empty rooms here (after a delay, to avoid race conditions)


                # --- Handle Timeout ---
                elif data.startswith("gameover|timeout"):
                    message_id = str(uuid.uuid4())
                    candidate_client = next((c for c in room["players"] if c["role"] == "candidate"), None)
                    hr_client = next((c for c in room["players"] if c["role"] == "hr"), None)

                    candidate_score = 0
                    hr_score = 0

                    if candidate_client and hr_client:
                        # Since no offer was made, we use default values (0, 0, 0) and an empty bonus_objective_id.
                        candidate_score = calculate_dynamic_candidate_score(
                            0, 0, 0, "", False, candidate_scoring_config
                        )
                        hr_score = calculate_dynamic_hr_score(
                            0, 0, 0, 0, "", False, hr_scoring_config
                        )
                    # Construct the extended gameover message for timeout
                    gameover_message = f"gameover|{message_id}|Negotiation timed out!|{candidate_score}|{hr_score}|{candidate_client['bonus_objective'] if candidate_client else 'N/A'}|{hr_client['bonus_objective'] if hr_client else 'N/A'}"

                    for client in room["players"]:  # Send to all players in the *room*
                        if client["is_active"]: # Check for active
                            await client["websocket"].send_text(gameover_message)
                    # Instead of clearing the room, mark clients as inactive
                    for client in room["players"]:
                        client["is_active"] = False

                # --- Handle Regular Chat Messages ---
                else:
                    message_id = str(uuid.uuid4())
                    for client in room["players"]:  # Broadcast to all players in the *room*
                        if client["is_active"]:#Check is active
                            if client["websocket"] != websocket:
                                await client["websocket"].send_text(f"msg|{message_id}|{current_client['player']}|{data}")
                            else:
                                await client["websocket"].send_text(f"ack|{message_id}|{current_client['player']}|{data}")

            except WebSocketDisconnect:
                logger.info(f"Client disconnected normally: {websocket.client}")
                break
            except Exception as e:
                logger.error(f"Error in message loop: {e}")
                break

    except WebSocketDisconnect:
        logger.info(f"Client disconnected during setup: {websocket.client}")
    except Exception as e:
        logger.error(f"Error in websocket endpoint: {e}")
    finally:
        # Cleanup code
        try:
            if room:  # Ensure room is assigned before accessing it
                current_client = next((c for c in room["players"] if c["websocket"] == websocket), None)
                if current_client:
                    current_client["is_active"] = False
                    if current_client in room["players"]:
                        room["players"].remove(current_client)
                    
            # Clean up empty rooms
            if room_id in rooms and not rooms[room_id]["players"]:
                logger.info(f"Removing empty room {room_id}")
                del rooms[room_id]
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")