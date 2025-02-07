from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uuid

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


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global player_counter

    await websocket.accept()

    # Assign a player number and store client info
    player_number = player_counter
    player_counter += 1
    client_info = {"websocket": websocket, "player": player_number}
    connected_clients.append(client_info)
    print(f"Client connected: {websocket.client}, Player {player_number}")

    # Send initial message with player number to the client
    await websocket.send_text(f"init:{player_number}")

    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received from Player {player_number}: {data}")

            # --- Handle Offer Messages ---
            if data.startswith("offer:"):
                offer_amount = data.split(":")[1]
                message_id = str(uuid.uuid4())

                # Broadcast the offer to all clients
                for client in connected_clients:
                    await client["websocket"].send_text(f"offer|{message_id}|{player_number}|Offer: ${offer_amount}")

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