from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.ws_manager import ws_manager

router = APIRouter(prefix="/ws", tags=["websocket"])

@router.websocket("/city-stream")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection open, client doesn't need to send data but we wait for heartbeats or client closure
            data = await websocket.receive_text()
            # If client sends ping, we reply pong
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)
