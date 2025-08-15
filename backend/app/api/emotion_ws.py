import json
from typing import Any, Dict, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Header, status
from app.config import settings
from app.tasks.emotion_ingest import persist_emotion_event

router = APIRouter(prefix="/ws", tags=["emotions"])

def _auth_ok(token_qs: Optional[str], token_hdr: Optional[str]) -> bool:
    expected = getattr(settings, "ingest_token", None) or ""
    incoming = token_qs or token_hdr or ""
    return expected and (incoming == expected)

@router.websocket("/emotions")
async def emotions_ws(
    websocket: WebSocket,
    token: Optional[str] = Query(default=None),
    x_auth_token: Optional[str] = Header(default=None)
):
    # Basic token check before accepting (avoid open WS)
    if not _auth_ok(token, x_auth_token):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_text()
            try:
                payload = json.loads(message)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"status": "error", "error": "invalid_json"}))
                continue

            # Normalize envelope (very permissive; only user_id is required)
            user_id = payload.get("user_id")
            if not user_id:
                await websocket.send_text(json.dumps({"status": "error", "error": "missing user_id"}))
                continue

            event = {
                "user_id": user_id,
                "session_id": payload.get("session_id"),
                "source": payload.get("source"),                   # e.g., "text"
                "emotion_label": payload.get("emotion_label"),     # e.g., "joy"
                "valence": payload.get("valence"),
                "arousal": payload.get("arousal"),
                "confidence": payload.get("confidence"),
                "timestamp": payload.get("timestamp"),
                "raw_payload": payload,                            # keep original message
            }

            # Hand off to Celery (non-blocking)
            task = persist_emotion_event.delay(event)
            await websocket.send_text(json.dumps({"status": "queued", "task_id": task.id}))
    except WebSocketDisconnect:
        # client disconnected
        pass
