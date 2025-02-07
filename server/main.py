from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS for HTTP requests (not WebSocket)
origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

connected_clients = []

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Manually check origin (critical for security)
    origin = websocket.headers.get("origin")
    if origin not in origins:
        await websocket.close(code=403)
        return

    await websocket.accept()
    print(f"Client connected: {websocket.client}")
    connected_clients.append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received: {data}")
            # Broadcast message to all clients (example)
            for client in connected_clients:
                await client.send_text(f"Echo: {data}")

    except WebSocketDisconnect:
        print(f"Client disconnected: {websocket.client}")
        connected_clients.remove(websocket)