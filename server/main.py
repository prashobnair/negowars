from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uuid
import random

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
# No more MAX_ROUNDS


@app.get("/")
async def root():
    return {"message": "Hello World"}

def calculate_candidate_score(salary, bonus, remote_days, hidden_objective, success):
    score = 0

    # Base Salary
    if salary >= 65000:
        score += 20
        salary_above_65k = salary - 65000
        score += min(40, int(salary_above_65k / 1000) * 3)  # +3 points per $1000, up to $75k
        if salary >= 75000:
          score += min(20, int((salary - 75000)/ 1000) * 2) # bonus, +2 per 1000 above 75000

    # Sign-On Bonus
    if bonus >= 5000:
        score += 20
        bonus_above_5k = bonus - 5000
        score += min(20, int(bonus_above_5k / 500) * 4) #+4 points per 500, up to 8k+
        if bonus >= 8000:
            score += min(20, int((bonus - 8000) / 500) * 5)

    # Remote Work Days
    if remote_days >= 2:
        score += 10
        if remote_days >= 3:
          score += 10 #bonus points

    # Outcome Modifier
    if success:
        score += 50
    else:
        score -= 50

    # Hidden Objective Bonus
    if hidden_objective == "debt" and bonus >= 7000:
        score += 30
    elif hidden_objective == "growth":
        score += 20  # Placeholder for now

    return score


def calculate_hr_score(salary, bonus, remote_days, total_compensation, hidden_objective, success):
    score = 0

    # Base Salary
    if salary <= 65000:
        score += 30
    else:
      score += max(-20, 30 - (int((salary - 65000) / 1000) * 2))
    if salary > 75000:
        score = -20 #flat -20 if salary > 75000

    # Sign-On Bonus
    if bonus <= 5000:
        score += 20
    else:
      score += max(-10, 20 - (int((bonus - 5000) / 500) * 2))
    if bonus > 8000:
      score = -10

    # Total Compensation
    if total_compensation <= 80000:
        score += 30
    else:
        score += max(-20, 30 - (int((total_compensation - 80000) / 1000) * 3))
    if total_compensation > 85000:
        score = -20

    # Remote Work Days
    if remote_days == 0:
        score += 10
    elif remote_days == 1:
        score += 5

    # Outcome Modifier
    if success:
        score += 50
    else:
        score -= 50

    # Hidden Objective Bonus
    if hidden_objective == "quick" and success: # Assuming success is determined elsewhere
        score += 30
    elif hidden_objective == "budget" and total_compensation < 76000 :
        score += 30

    return score

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global player_counter
    global connected_clients

    await websocket.accept()

    # Assign a player number and store client info
    player_number = player_counter
    player_counter += 1
    client_info = {"websocket": websocket, "player": player_number, "role":None, "hidden_objective":None, "salary": None, "bonus":None, "remote_days": None}
    connected_clients.append(client_info)
    print(f"Client connected: {websocket.client}, Player {player_number}")

    # Determine the role (Candidate or HR) based on player number
    role = "candidate" if player_number % 2 != 0 else "hr"
    client_info["role"] = role #set the role here.

    # --- Assign a *random* hidden objective ---
    if role == "candidate":
        hidden_objectives = ["debt", "growth"]  # The IDs of the candidate objectives
    else:
        hidden_objectives = ["quick", "budget"]  # The IDs of the HR objectives
    chosen_objective = random.choice(hidden_objectives)
    client_info["hidden_objective"] = chosen_objective


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
                _, offer_data = data.split(":", 1)  # Split only on the first colon
                salary, bonus, remote_days = offer_data.split(",")  # Split into 3 parts
                # Find the client info and update offer
                for client in connected_clients:
                    if client["websocket"] == websocket:
                        client["salary"] = int(salary)
                        client["bonus"] = int(bonus)
                        client["remote_days"] = int(remote_days)
                        break # Found the right client

                message_id = str(uuid.uuid4())

                # Broadcast the offer to all clients
                for client in connected_clients:
                    await client["websocket"].send_text(f"offer|{message_id}|{player_number}|Offer: ${salary},Bonus: ${bonus},Remote Days: {remote_days}")

            # --- Handle "accept" Message ---
            elif data == "accept":
                message_id = str(uuid.uuid4())

                # --- Calculate Scores (Before sending gameover) ---
                candidate_score = 0
                hr_score = 0
                # Find the candidate and HR clients
                candidate_client = next((c for c in connected_clients if c["role"] == "candidate"), None)
                hr_client = next((c for c in connected_clients if c["role"] == "hr"), None)

                if candidate_client and hr_client: #Make sure clients are present
                    # Calculate scores only if negotiation was successful
                  if candidate_client["salary"] is not None: #This will be set only on offers
                    candidate_score = calculate_candidate_score(
                        candidate_client["salary"],
                        candidate_client["bonus"],
                        candidate_client["remote_days"],
                        candidate_client["hidden_objective"],
                        True  # Negotiation was successful
                    )
                    hr_score = calculate_hr_score(
                        candidate_client["salary"], #salary
                        candidate_client["bonus"], #bonus
                        candidate_client["remote_days"], #remote days
                        candidate_client["salary"] + candidate_client["bonus"],  # Total compensation
                        hr_client["hidden_objective"],
                        True  # Negotiation was successful
                    )

                # Construct the extended gameover message
                gameover_message = f"gameover|{message_id}|Negotiation successful!|{candidate_score}|{hr_score}|{candidate_client['hidden_objective'] if candidate_client else 'N/A'}|{hr_client['hidden_objective'] if hr_client else 'N/A'}"
                for client in connected_clients:
                    await client["websocket"].send_text(gameover_message)

                connected_clients = []  # Clear connected clients (end game)
                player_counter = 1 # Reset

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