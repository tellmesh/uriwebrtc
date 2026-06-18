# uriwebrtc

`webrtc://` URI capability pack for [urisys-node](https://github.com/tellmesh/urisys-node).

Transport layer for WebRTC sessions: **HTTP signaling inbox** (mock relay on node) and **DataChannel URI envelopes**. Browser P2P signaling between ifURI peers uses ifURI's `/api/webrtc/signal` — see [if-uri/app/docs/WEBRTC.md](https://github.com/if-uri/app/blob/main/docs/WEBRTC.md).

## Install

**PyPI / GitHub Releases** (urisys-node auto-install):

```bash
urisys-node remote install-pack webrtc --endpoint http://lenovo:8790
```

**Dev wheel**:

```bash
pip wheel -w /tmp/wheels .
node://lenovo/command/install-pack  # pack: webrtc, specs: [file:///tmp/wheels/uriwebrtc-0.1.0-py3-none-any.whl]
```

Flow: `urisys-examples/lenovo-remote/02c-install-webrtc-pack.uri.flow.yaml`

## Routes

| URI | Operation | Description |
|-----|-----------|-------------|
| `webrtc://local/session/{session}/command/start` | `webrtc.session.start` | Open session (`signaling: http-relay`) |
| `webrtc://local/session/{session}/data/command/send` | `webrtc.data.send` | Accept URI envelope (no execution) |
| `webrtc://local/session/{session}/signal/command/post` | `webrtc.signal.post` | Store SDP/ICE signal in room inbox |
| `webrtc://local/session/{session}/signal/query/inbox` | `webrtc.signal.inbox` | Poll signals since `id` |

Manifest: [`uriwebrtc/manifest.yaml`](uriwebrtc/manifest.yaml)  
Contract: [`markpacts/uriwebrtc.markpact.md`](markpacts/uriwebrtc.markpact.md)

## Payloads

### Session start

```json
{ "room": "rdp-chat" }
```

Response:

```json
{
  "ok": true,
  "webrtc": {
    "room": "rdp-chat",
    "status": "ready",
    "signaling": "http-relay",
    "data_channel": "uri-envelope"
  }
}
```

### Data send (URI envelope)

```json
{
  "room": "rdp-chat",
  "envelope": {
    "uri": "kvm://local/monitor/primary/query/screenshot",
    "payload": {},
    "context": { "approved": true, "dry_run": true }
  }
}
```

Execution stays in target schemes (`kvm://`, `him://`, …) — this route only records the envelope.

### Signal post

```json
{
  "room": "rdp-chat",
  "from": "http://192.168.188.212:8766",
  "type": "offer",
  "data": { "type": "offer", "sdp": "v=0..." }
}
```

`type`: `offer` | `answer` | `ice`

### Signal inbox

```json
{ "room": "rdp-chat", "since": 0 }
```

## ifURI integration

When two [ifURI](https://github.com/if-uri/app) `/voice` tabs connect as **WebRTC peers**:

1. SDP/ICE via `POST {peer}/api/webrtc/signal` (browser ↔ browser through ifURI HTTP relay)
2. Duplex mic/audio via `RTCPeerConnection`
3. Voice commands via data channel: `{ kind: "voice", id, text }` → peer runs local voice pipeline → `{ kind: "voice-reply", id, ok, text }`

Node `webrtc://` routes are used for **smoke tests** and **flow automation**, not for browser signaling path.

## Development

```bash
cd tellmesh/uriwebrtc
uv sync
pytest -q
```

## Related

- [urisys-node pack_resolver](https://github.com/tellmesh/urisys-node) — `webrtc` → `uriwebrtc`
- [uristt](https://github.com/tellmesh/uristt) — `stt://` / `tts://` (voice on node)

## Ekosystem TellMesh

Orchestrator: **[urisys](https://github.com/tellmesh/urisys)** · Mapa: **[MESH.md](https://github.com/tellmesh/urisys/blob/main/docs/MESH.md)** · Model: **[ECOSYSTEM.md](https://github.com/tellmesh/urisys/blob/main/../docs/ECOSYSTEM.md)**

| Pole | Wartość |
|------|---------|
| **Warstwa** | Capability pack |
| **Scheme** | `webrtc://` |
| **Zależność** | `uricore>=0.1.8` |

Runtime edge: **`uri_control.edge`** w pakiecie **`uricore`** (legacy `urisysedge` usunięty 2026-06).
Router intencji: **`urirouter`** (`uri_router`) — resolve + HTTP/MQTT delegate.

<!-- end-ecosystem -->
