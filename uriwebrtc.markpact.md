# UriPack: uriwebrtc

Self-contained Markpact — definitions, full source, run config. Unpack & run: `urisys markpact run uriwebrtc/uriwebrtc.markpact.md --as service` (writes `.markpact/`).

```yaml markpact:pack
apiVersion: urisys.io/v1
kind: UriPack
metadata:
  id: uriwebrtc-pack
  version: 1.0.0
  language: python
description: WebRTC session — HTTP signaling inbox (node) and DataChannel URI envelopes; browser P2P via ifURI.
schemes:
- webrtc
capabilities:
- id: webrtc.session.start
  uri: webrtc://local/session/{session}/command/start
  kind: command
  operation: webrtc.session.start
  handler: python://uriwebrtc.handlers:session_start
  side_effects: true
  approval: required
- id: webrtc.data.send
  uri: webrtc://local/session/{session}/data/command/send
  kind: command
  operation: webrtc.data.send
  handler: python://uriwebrtc.handlers:data_send
  side_effects: true
  approval: required
- id: webrtc.signal.post
  uri: webrtc://local/session/{session}/signal/command/post
  kind: command
  operation: webrtc.signal.post
  handler: python://uriwebrtc.handlers:signal_post
  side_effects: true
  approval: required
- id: webrtc.signal.inbox
  uri: webrtc://local/session/{session}/signal/query/inbox
  kind: query
  operation: webrtc.signal.inbox
  handler: python://uriwebrtc.handlers:signal_inbox
  side_effects: false
  approval: not_required
policy:
  default: deny_mutations_without_approval
runtime:
  default_environment: mock
  supports:
  - mock
  - local
  - docker
```

```yaml markpact:run
modes:
- pack
- service
- flow
- interface
- adapter
default: service
scheme: webrtc
service:
  port: 8790
  wire: POST /uri/call
flow:
  ids: []
adapter:
  wire: POST /uri/call
  events: GET /events
```

```python markpact:module path=uriwebrtc/__init__.py
from __future__ import annotations

from importlib.resources import files

from .routes import register

__all__ = ["register", "manifest_path"]


def manifest_path():
    return files(__package__).joinpath("manifest.yaml")
```

```python markpact:module path=uriwebrtc/handlers.py
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
```

```python markpact:module path=uriwebrtc/routes.py
from __future__ import annotations

from importlib.resources import files

from urisysedge.manifest import register_manifest_file


def register(rt):
    register_manifest_file(rt, files(__package__).joinpath("manifest.yaml"))
```

```markdown markpact:docs
# uriwebrtc

`webrtc://` URI capability pack — HTTP signaling relay and DataChannel URI envelopes.

Standalone package (like `urihim`), consumed by `urisys-node`.

**Browser duplex voice** between two ifURI `/voice` instances uses ifURI `GET/POST /api/webrtc/signal` and data-channel `voice` / `voice-reply` messages — see [if-uri/app/docs/WEBRTC.md](https://github.com/if-uri/app/blob/main/docs/WEBRTC.md).

Node `webrtc://` routes are for flows, smoke tests, and envelope capture — not the live browser SDP path.
```

