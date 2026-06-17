from __future__ import annotations

import time
from typing import Any

_ROOMS: dict[str, dict[str, Any]] = {}
_SIGNALS: dict[str, list[dict[str, Any]]] = {}
_MAX_SIGNALS = 500


def _room_id(context: dict[str, Any]) -> str:
    params = context.get("params") or {}
    return params.get("session") or params.get("room") or "rdp-chat"


def session_start(payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    room = payload.get("room") or _room_id(context)
    entry = {
        "room": room,
        "status": "ready",
        "signaling": "http-relay",
        "data_channel": "uri-envelope",
    }
    _ROOMS[room] = entry
    return {"ok": True, "webrtc": entry, "note": "Session ready; use signal/post + signal/inbox for SDP/ICE relay."}


def data_send(payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    room = payload.get("room") or _room_id(context)
    envelope = payload.get("envelope") or {}
    _ROOMS.setdefault(room, {"room": room, "status": "ready"})
    return {
        "ok": True,
        "room": room,
        "envelope": envelope,
        "received": True,
        "hint": "Forward envelope to chat://local/uri/command/execute for execution.",
    }


def signal_post(payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    room = payload.get("room") or _room_id(context)
    from_peer = str(payload.get("from") or "").strip()
    signal_type = str(payload.get("type") or "").strip().lower()
    data = payload.get("data")
    if not room or not from_peer or signal_type not in {"offer", "answer", "ice"}:
        return {"ok": False, "error": "room, from, type (offer|answer|ice) required"}
    inbox = _SIGNALS.setdefault(room, [])
    sig_id = len(inbox) + 1
    row = {
        "id": sig_id,
        "room": room,
        "from": from_peer,
        "type": signal_type,
        "data": data,
        "at": time.time(),
    }
    inbox.append(row)
    if len(inbox) > _MAX_SIGNALS:
        _SIGNALS[room] = inbox[-_MAX_SIGNALS:]
    _ROOMS.setdefault(room, {"room": room, "status": "signaling"})
    return {"ok": True, "id": sig_id, "room": room}


def signal_inbox(payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    room = payload.get("room") or _room_id(context)
    since = max(0, int(payload.get("since") or 0))
    if not room:
        return {"ok": False, "error": "room required"}
    inbox = _SIGNALS.get(room, [])
    pending = [s for s in inbox if int(s.get("id") or 0) > since]
    next_id = int(inbox[-1]["id"]) if inbox else since
    return {"ok": True, "room": room, "signals": pending, "since": since, "next": next_id}
