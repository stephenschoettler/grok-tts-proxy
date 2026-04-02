# grok-tts-proxy

A lightweight local proxy that exposes xAI's Grok TTS voices via an **OpenAI-compatible `/v1/audio/speech` endpoint**.

Drop it in front of any app that already speaks the OpenAI TTS API — Home Assistant, OpenWebUI, Hermes, OpenClaw, custom scripts — and get Grok voices without changing the client.

---

## Why it exists

xAI's TTS API (`https://api.x.ai/v1/tts`) uses a slightly different request shape than OpenAI's `/v1/audio/speech`. This proxy translates the OpenAI format to Grok's format so you can point any OpenAI-TTS-compatible tool at `http://localhost:7902` and it just works.

Zero external dependencies. Single Python file. 140 lines.

---

## Quickstart

### 1. Clone

```bash
git clone https://github.com/stephenschoettler/grok-tts-proxy.git
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

| Variable        | Default      | Description                |
|-----------------|--------------|----------------------------|
| `XAI_API_KEY`   | *(required)* | Your xAI API key           |
| `GROK_TTS_PORT` | `7902`       | Port the proxy listens on  |

---

## Voices

Five expressive voices, each with a distinct personality:

| Voice ID | Tone | Best for |
|----------|------|----------|
| **`eve`** | Energetic, upbeat | Demos, announcements, upbeat content (default) |
| **`ara`** | Warm, friendly | Conversational interfaces, customer support |
| **`rex`** | Confident, clear | Business presentations, tutorials |
| **`sal`** | Smooth, balanced | Versatile — works across content types |
| **`leo`** | Authoritative, strong | Instructions, narration, educational content |

Voice IDs are case-insensitive. The proxy passes unknown voices through unchanged, and the `VOICE_MAP` dict in the script lets you alias OpenAI voice names (e.g. map `"alloy"` → `"leo"`).

[Preview all voices →](https://x.ai/api/voice)

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
- `input` — the text to synthesize *(required, max 15,000 characters)*
- `voice` — Grok voice ID, or an alias defined in `VOICE_MAP`

**Response:** raw audio bytes (MP3 at 24 kHz / 128 kbps by default)

### Speech tags

Grok TTS supports inline expression tags that pass straight through the proxy:

```json
{"input": "So I walked in and [pause] there it was. [laugh] I could not believe it!"}
```

```json
{"input": "I need to tell you something. <whisper>It is a secret.</whisper> Pretty cool, right?"}
```

**Inline tags:** `[laugh]`, `[chuckle]`, `[cry]`, `[sigh]`, `[gasp]`, `[pause]`, `[cough]`, `[sniffle]`, `[groan]`

**Wrapping tags:** `<whisper>`, `<shout>`, `<sing>`, `<fast>`, `<slow>`, `<high_pitch>`, `<low_pitch>`

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

mpv hello.mp3   # or: aplay, ffplay, vlc, etc.
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

### Hermes / OpenClaw

In your TTS config, set:

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

## Supported languages

Grok TTS supports 20 languages. The proxy passes `language` as `"en"` by default — edit the `grok_payload` dict in the script to change it.

`en` · `zh` · `ja` · `ko` · `de` · `fr` · `it` · `es-ES` · `es-MX` · `pt-BR` · `pt-PT` · `ru` · `tr` · `hi` · `bn` · `id` · `vi` · `ar-EG` · `ar-SA` · `ar-AE` · `auto`

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

Python 3 standard library only (`http.server`, `urllib`, `json`, `os`, `sys`). No `pip install` needed.

---

## Links

- [xAI TTS documentation](https://docs.x.ai/developers/model-capabilities/audio/text-to-speech)
- [Voice demos & playground](https://x.ai/api/voice)
- [Get an xAI API key](https://console.x.ai/team/default/api-keys)

---

## License

MIT — see [LICENSE](LICENSE).
