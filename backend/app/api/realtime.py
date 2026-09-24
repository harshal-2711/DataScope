"""WebSocket Endpoint for Real-Time Multi-Tenant Workspace Events."""
from __future__ import annotations

import logging
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.security import decode_token
from app.db.session import SessionLocal
from app.models.membership import CompanyMembership
from app.services.realtime_manager import realtime_manager

router = APIRouter(tags=["Real-Time"])
logger = logging.getLogger("datascope.ws")


@router.websocket("/ws/{company_id}")
async def websocket_company_channel(
    websocket: WebSocket,
    company_id: str,
    token: str = Query(None),
):
    """Authenticate and maintain a live real-time connection for the company workspace."""
    # Optional token validation for browser WebSocket clients
    user_id = None
    if token:
        payload = decode_token(token)
        if payload and payload.get("type") == "access":
            user_id = payload.get("sub")

    # Connect client
    await realtime_manager.connect(company_id, websocket)

    try:
        while True:
            # Keep-alive heartbeat listener
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text('{"type": "pong"}')
    except WebSocketDisconnect:
        realtime_manager.disconnect(company_id, websocket)
    except Exception as err:
        logger.warning("WebSocket error in company channel %s: %s", company_id, err)
        realtime_manager.disconnect(company_id, websocket)
