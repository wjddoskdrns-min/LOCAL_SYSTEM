# app/services/room_manager.py
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from enum import Enum
import secrets
from typing import Dict, Optional, Any


UTC = timezone.utc


class RoomState(str, Enum):
    CREATED = "CREATED"
    ACTIVE = "ACTIVE"
    DESTROYED = "DESTROYED"
    EXPIRED = "EXPIRED"


@dataclass(frozen=True)
class Room:
    room_id: str
    created_at: datetime
    expires_at: datetime
    scope: str
    mode: str
    state: RoomState
    request_id: str


class RoomManager:
    """
    Room TTL + One-way Dissolution
    - Every EXECUTE gets a NEW room.
    - Room never merges into SSOT.
    - TTL enforced regardless of approval/execution outcome.
    - Destroyed/Expired rooms are terminal.
    """

    def __init__(self) -> None:
        self._rooms: Dict[str, Room] = {}

    def _now(self) -> datetime:
        return datetime.now(tz=UTC)

    def create_room(self, *, scope: str, mode: str, ttl_sec: int, request_id: str) -> Room:
        now = self._now()
        room_id = secrets.token_hex(8)
        room = Room(
            room_id=room_id,
            created_at=now,
            expires_at=now + timedelta(seconds=max(1, int(ttl_sec))),
            scope=scope,
            mode=mode,
            state=RoomState.CREATED,
            request_id=request_id,
        )
        self._rooms[room_id] = room
        return room

    def get_room(self, room_id: str) -> Optional[Room]:
        room = self._rooms.get(room_id)
        if not room:
            return None
        # TTL enforcement on read
        if room.state not in (RoomState.DESTROYED, RoomState.EXPIRED) and self._now() > room.expires_at:
            expired = Room(**{**asdict(room), "state": RoomState.EXPIRED})
            self._rooms[room_id] = expired
            return expired
        return room

    def activate(self, room_id: str) -> Room:
        room = self.get_room(room_id)
        if room is None:
            raise KeyError("room_not_found")
        if room.state in (RoomState.DESTROYED, RoomState.EXPIRED):
            raise RuntimeError("room_terminal_state")
        active = Room(**{**asdict(room), "state": RoomState.ACTIVE})
        self._rooms[room_id] = active
        return active

    def destroy(self, room_id: str) -> Room:
        room = self.get_room(room_id)
        if room is None:
            raise KeyError("room_not_found")
        # One-way dissolution: terminal
        terminal = Room(**{**asdict(room), "state": RoomState.DESTROYED})
        self._rooms[room_id] = terminal
        return terminal

    def as_dict(self, room_id: str) -> Dict[str, Any]:
        room = self.get_room(room_id)
        if room is None:
            return {"ok": False, "error": "room_not_found"}
        d = asdict(room)
        # JSON-friendly timestamps
        d["created_at"] = room.created_at.isoformat()
        d["expires_at"] = room.expires_at.isoformat()
        d["state"] = room.state.value
        return {"ok": True, "room": d}
