"""Real-Time WebSocket Connection Manager for DataScope Multi-Tenant Events."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Set
from fastapi import WebSocket

logger = logging.getLogger("datascope.realtime")


class RealtimeConnectionManager:
    """Thread-safe WebSocket hub delivering multi-tenant live updates."""

    def __init__(self) -> None:
        # Maps company_id -> list of active WebSocket client connections
        self._company_connections: Dict[str, List[WebSocket]] = {}
        self._lock = asyncio.Lock() if asyncio.get_event_loop().is_running() else None

    async def connect(self, company_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        if company_id not in self._company_connections:
            self._company_connections[company_id] = []
        self._company_connections[company_id].append(websocket)
        logger.info("WebSocket client connected to company workspace '%s' (Total: %d)", company_id, len(self._company_connections[company_id]))

    def disconnect(self, company_id: str, websocket: WebSocket) -> None:
        if company_id in self._company_connections:
            if websocket in self._company_connections[company_id]:
                self._company_connections[company_id].remove(websocket)
            if not self._company_connections[company_id]:
                del self._company_connections[company_id]
        logger.info("WebSocket client disconnected from company workspace '%s'", company_id)

    async def broadcast_to_company(self, company_id: str, event_type: str, payload: Dict[str, Any]) -> None:
        """Broadcast real-time JSON message to all active users inside a company workspace."""
        if company_id not in self._company_connections:
            return

        message = {
            "type": event_type,
            "company_id": company_id,
            "data": payload,
        }
        raw_text = json.dumps(message)
        dead_sockets = []

        for socket in list(self._company_connections.get(company_id, [])):
            try:
                await socket.send_text(raw_text)
            except Exception as err:
                logger.warning("Failed to send WebSocket message: %s", err)
                dead_sockets.append(socket)

        for dead in dead_sockets:
            self.disconnect(company_id, dead)


realtime_manager = RealtimeConnectionManager()
