# grok-tts-proxy

A lightweight local proxy that exposes xAI's Grok TTS voices via an **OpenAI-compatible `/v1/audio/speech` endpoint**.

Drop it in front of any app that already speaks the OpenAI TTS API — Home Assistant, OpenWebUI, Hermes, OpenClaw, custom scripts — and get Grok voices without changing the client.

---

## Why it exists

xAI's TTS API (`https://api.x.ai/v1/tts`) uses a slightly different request shape than OpenAI's `/v1/audio/speech`. This proxy translates the OpenAI format to Grok's format so you can point any OpenAI-TTS-compatible tool at `http://localhost:7902` and it just works.

Zero external dependencies. Single Python file. ~150 lines.

---

## Quickstart

### 1. Clone / copy the script

```bash
git clone <this-repo> grok-tts-proxy
cd grok-tts-proxy
```

### 2. Set your API key

```bash
cp .env.example .env
# Edit .env and fill in your XAI_API_KEY
```

### 3. Run it

```bash
XAI_API_KEY=xai-your-key-here python3 grok-tts-proxy.py
# or: source .env && python3 grok-tts-proxy.py
```

The proxy listens on **port 7902** by default.

---

## Environment variables

| Variable        | Default                      | Description                          |
|-----------------|------------------------------|--------------------------------------|
| `XAI_API_KEY`   | *(required)*                 | Your xAI API key                     |
| `GROK_TTS_PORT` | `7902`                       | Port the proxy listens on            |

---

## Supported voices

Grok TTS supports these voice IDs. Pass any of them in the `voice` field:

| Voice ID | Character        |
|----------|-----------------|
| `leo`    | Male, natural   |
| `eve`    | Female, natural |
| `ara`    | Female          |
| `rex`    | Male            |
| `sal`    | Male            |

You can pass any voice ID directly — the proxy passes unknown voices through unchanged. The `VOICE_MAP` dict in the script lets you alias OpenAI voice names (e.g. map `"alloy"` → `"leo"`).

---

## API

### `POST /v1/audio/speech`

OpenAI-compatible endpoint.

**Request body (JSON):**

```json
{
  "model": "tts-1",
  "input": "Hello, world!",
  "voice": "leo"
}
```

- `model` — ignored (Grok only has one TTS model)
- `input` — the text to synthesize *(required)*
- `voice` — Grok voice ID, or an alias defined in `VOICE_MAP`

**Response:** raw audio bytes (`audio/mpeg` or whatever Grok returns)

### `GET /health`

Returns `{"status":"ok","proxy":"grok-tts","port":7902}` — useful for service health checks.

---

## curl example

```bash
curl http://localhost:7902/v1/audio/speech \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"model":"tts-1","input":"Hello from Grok!","voice":"eve"}' \
  --output hello.mp3

mpv hello.mp3   # or: aplay hello.mp3 / ffplay hello.mp3
```

---

## Client configuration examples

### OpenAI Python client

```python
from openai import OpenAI

client = OpenAI(
    api_key="not-used",          # proxy doesn't check this
    base_url="http://localhost:7902/v1",
)

with client.audio.speech.with_streaming_response.create(
    model="tts-1",
    voice="leo",
    input="Hello from Grok via OpenAI client!",
) as response:
    response.stream_to_file("output.mp3")
```

### Hermes (OpenClaw TTS plugin)

In your Hermes / OpenClaw TTS config, set:

```
TTS Provider: OpenAI-compatible
Base URL:     http://localhost:7902/v1
API Key:      (any value — not validated)
Voice:        leo
```

### OpenWebUI

Settings → Audio → TTS:
- **Engine:** OpenAI
- **API Base URL:** `http://localhost:7902/v1`
- **API Key:** `not-used`
- **Voice:** `leo`

---

## Running as a systemd user service

Copy the included service file and enable it:

```bash
cp grok-tts-proxy.service ~/.config/systemd/user/
# Edit the file: update ExecStart path and EnvironmentFile path if needed
systemctl --user daemon-reload
systemctl --user enable --now grok-tts-proxy
systemctl --user status grok-tts-proxy
```

Check logs:

```bash
journalctl --user -u grok-tts-proxy -f
```

---

## No external dependencies

The proxy uses only Python 3 standard library modules (`http.server`, `urllib`, `json`, `os`, `sys`). No `pip install` needed.

---

## License

MIT — see [LICENSE](LICENSE).
