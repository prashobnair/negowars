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

connected_clients = []

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.websocket("/ws")  # Changed back to @app.websocket
async def websocket_endpoint(websocket: WebSocket):  # Use WebSocket, not Request
    await websocket.accept()
    print(f"Client connected: {websocket.client}")
    connected_clients.append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received: {data}")

            # Generate a unique message ID
            message_id = str(uuid.uuid4())

            # Send confirmation back to the sender
            await websocket.send_text(f"ack:{message_id}:{data}")

            # Broadcast to all other clients
            for client in connected_clients:
                if client != websocket:
                    await client.send_text(f"msg:{message_id}:{data}")

    except WebSocketDisconnect:
        print(f"Client disconnected: {websocket.client}")
        connected_clients.remove(websocket)
    except Exception as e:
        print(f"An error occurred: {e}")