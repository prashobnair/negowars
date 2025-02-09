from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uuid
import random
import math
import logging
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

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global player_counter
    global connected_clients

    await websocket.accept()

    # Assign a player number and store client info
    player_number = player_counter
    player_counter += 1
    client_info = {"websocket": websocket, "player": player_number, "role":None, "bonus_objective":None, "salary": None, "bonus":None, "remote_days": None}
    connected_clients.append(client_info)
    print(f"Client connected: {websocket.client}, Player {player_number}")

    # Determine the role (Candidate or HR) based on player number
    role = "candidate" if player_number % 2 != 0 else "hr"
    client_info["role"] = role #set the role here.

    # --- Assign a *random* bonus objective ---
    if role == "candidate":
        bonus_objectives = ["debt"]  # The IDs of the candidate objectives
    else:
        bonus_objectives = ["budget"]  # The IDs of the HR objectives
    chosen_objective = random.choice(bonus_objectives)
    client_info["bonus_objective"] = chosen_objective


    # Send initial message with player number to the client
    await websocket.send_text(f"init|{player_number}")

    # Send the role to the client
    await websocket.send_text(f"role|{role}")

    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received from Player {player_number}: {data}")

            # --- Handle Offer Messages ---
            if data.startswith("offer:"):
                try:
                    _, offer_data = data.split(":", 1)
                    salary_str, bonus_str, remote_days_str = offer_data.split(",")
                    
                    # Validate that all values are present and can be converted to integers
                    if not all([salary_str.strip(), bonus_str.strip(), remote_days_str.strip()]):
                        continue  # Skip processing if any value is empty
                    
                    salary = int(salary_str)
                    bonus = int(bonus_str)
                    remote_days = int(remote_days_str)
                    
                    # Find the client info and update offer
                    for client in connected_clients:
                        if client["websocket"] == websocket:
                            client["salary"] = salary
                            client["bonus"] = bonus
                            client["remote_days"] = remote_days
                            break

                    message_id = str(uuid.uuid4())

                    # Broadcast the offer to all clients
                    for client in connected_clients:
                        await client["websocket"].send_text(f"offer|{message_id}|{player_number}|Offer: ${salary},Bonus: ${bonus},Remote Days: {remote_days}")
                except (ValueError, IndexError) as e:
                    print(f"Invalid offer format: {e}")
                    continue

            # --- Handle "accept" Message ---
            elif data == "accept":
                message_id = str(uuid.uuid4())
                logger.info(f"Received 'accept' message. Message ID: {message_id}")
                
                # Find the client sending the "accept" message.  THIS IS CRUCIAL.
                current_client = next((c for c in connected_clients if c["websocket"] == websocket), None)
                if not current_client:
                    logger.warning("Received 'accept' from unknown client.")
                    continue  # Skip if client not found

                # --- Calculate Scores (Before sending gameover) ---
                candidate_score = 0
                hr_score = 0
                # Find the candidate and HR clients
                candidate_client = next((c for c in connected_clients if c["role"] == "candidate"), None)
                hr_client = next((c for c in connected_clients if c["role"] == "hr"), None)
                logger.info(f"Candidate client: {candidate_client}")
                logger.info(f"HR client: {hr_client}")

                if candidate_client and hr_client: #Make sure clients are present
                    logger.info("Both candidate and HR clients found.")
                    
                    # Determine the client who *made* the offer (the one who *didn't* accept)
                    offering_client = candidate_client if current_client["role"] == "hr" else hr_client

                    # Calculate scores only if negotiation was successful
                    if offering_client["salary"] is not None:  # Check the *offering* client
                        logger.info("Calculating scores...")
                        try:
                            candidate_score = calculate_dynamic_candidate_score(
                                offering_client["salary"],  # Use offering client's values
                                offering_client["bonus"],
                                offering_client["remote_days"],
                                candidate_client["bonus_objective"],  # Candidate's bonus objective
                                True,
                                candidate_scoring_config  # Pass the correct config!
                            )
                            logger.info(f"Candidate score calculated: {candidate_score}")

                            hr_score = calculate_dynamic_hr_score(
                                offering_client["salary"], # Use offering client's values
                                offering_client["bonus"],
                                offering_client["remote_days"],
                                offering_client["salary"] + offering_client["bonus"],  # Total compensation
                                hr_client["bonus_objective"],  # HR's bonus objective
                                True,
                                hr_scoring_config  # Pass the correct config!
                            )
                            logger.info(f"HR score calculated: {hr_score}")

                        except Exception as e:
                            logger.exception(f"Error during score calculation: {e}")
                    else:
                        logger.info("No offer made yet, skipping score calculation.")
                        candidate_score = 0  # Still initialize to 0
                        hr_score = 0 # Initialize to avoid errors
                else:
                    logger.warning("Either candidate or HR client not found.")
                    candidate_score = 0  # Still initialize to 0
                    hr_score = 0

                # Construct the extended gameover message
                logger.info("Constructing gameover message...")
                gameover_message = f"gameover|{message_id}|Negotiation successful!|{candidate_score}|{hr_score}|{candidate_client['bonus_objective'] if candidate_client else 'N/A'}|{hr_client['bonus_objective'] if hr_client else 'N/A'}"
                logger.info(f"Gameover message: {gameover_message}")
                for client in connected_clients:
                    try:
                        await client["websocket"].send_text(gameover_message)
                        logger.info(f"Sent gameover message to: {client['player']}")
                    except Exception as e:
                        logger.exception(f"Error sending gameover message to client {client['player']}: {e}")
                connected_clients = []  # Clear connected clients (end game)
                player_counter = 1 # Reset
            # --- Handle Timeout ---
            elif data.startswith("gameover|timeout"):  # Correctly handle the timeout message
                message_id = str(uuid.uuid4())
                candidate_client = next((c for c in connected_clients if c["role"] == "candidate"), None)
                hr_client = next((c for c in connected_clients if c["role"] == "hr"), None)

                candidate_score = 0
                hr_score = 0

                if candidate_client and hr_client:
                    #Calculate score. Negotiation failed, so pass success = False
                    candidate_score = calculate_dynamic_candidate_score(
                        candidate_client.get("salary",0), #get safe values
                        candidate_client.get("bonus",0),
                        candidate_client.get("remote_days",0),
                        candidate_client["bonus_objective"],
                        False,
                        candidate_scoring_config
                    )
                    hr_score = calculate_dynamic_hr_score(
                        candidate_client.get("salary",0),
                        candidate_client.get("bonus", 0),
                        candidate_client.get("remote_days",0),
                        candidate_client.get("salary",0) + candidate_client.get("bonus",0),
                        hr_client["bonus_objective"],
                        False,
                        hr_scoring_config
                    )
                # Construct the extended gameover message for timeout
                gameover_message = f"gameover|{message_id}|Negotiation timed out!|{candidate_score}|{hr_score}|{candidate_client['bonus_objective'] if candidate_client else 'N/A'}|{hr_client['bonus_objective'] if hr_client else 'N/A'}"

                for client in connected_clients:
                    await client["websocket"].send_text(gameover_message)


                connected_clients = []
                player_counter = 1

            # --- Handle Regular Chat Messages ---
            else:
                message_id = str(uuid.uuid4())
                await websocket.send_text(f"ack|{message_id}|{player_number}|{data}")
                for client in connected_clients:
                    if client["websocket"] != websocket:
                        await client["websocket"].send_text(f"msg|{message_id}|{player_number}|{data}")

    except WebSocketDisconnect:
        print(f"Client disconnected: {websocket.client}, Player {player_number}")
        for i, client in enumerate(connected_clients):
            if client["websocket"] == websocket:
                del connected_clients[i]
                break
    except Exception as e:
        print(f"An error occurred: {e}")