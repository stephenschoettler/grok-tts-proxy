#!/usr/bin/env python3
"""
Grok TTS Proxy — translates OpenAI TTS API requests to Grok's TTS API.

Listens on port 7902 (configurable via GROK_TTS_PORT).
Accepts POST /v1/audio/speech with OpenAI format, forwards to
https://api.x.ai/v1/tts and returns the audio bytes.

Voice mapping: OpenAI voice field → Grok voice_id (pass-through by default).
"""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

import urllib.request
import urllib.error

PORT = int(os.getenv("GROK_TTS_PORT", "7902"))
XAI_API_KEY = os.getenv("XAI_API_KEY", "")
GROK_TTS_URL = "https://api.x.ai/v1/tts"

# Optional: map OpenAI voice names to Grok voice IDs.
# By default, the voice field is passed through unchanged.
# Add entries here if you want aliases (e.g. "alloy" -> "leo").
VOICE_MAP = {
    "leo": "leo",
    "eve": "eve",
}


class GrokTTSHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        print(f"[grok-tts-proxy] {self.address_string()} - {fmt % args}", flush=True)

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(
                json.dumps({"status": "ok", "proxy": "grok-tts", "port": PORT}).encode()
            )
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path not in ("/v1/audio/speech", "/v1/audio/speech/"):
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error":"not found"}')
            return

        # Read request body
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b"{}"

        try:
            req_data = json.loads(body)
        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error":"invalid json"}')
            return

        # Translate OpenAI → Grok format
        openai_voice = req_data.get("voice", "leo")
        grok_voice = VOICE_MAP.get(openai_voice, openai_voice)  # pass-through if not in map
        text = req_data.get("input", "")

        if not text:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error":"input field required"}')
            return

        grok_payload = json.dumps({
            "text": text,
            "voice_id": grok_voice,
            "language": "en",
        }).encode()

        grok_req = urllib.request.Request(
            GROK_TTS_URL,
            data=grok_payload,
            headers={
                "Authorization": f"Bearer {XAI_API_KEY}",
                "Content-Type": "application/json",
                # Cloudflare blocks Python's default urllib user-agent
                "User-Agent": "curl/8.0",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(grok_req, timeout=30) as resp:
                audio_bytes = resp.read()
                content_type = resp.headers.get("Content-Type", "audio/mpeg")
        except urllib.error.HTTPError as e:
            err_body = e.read()
            print(f"[grok-tts-proxy] Grok API error {e.code}: {err_body[:200]}", flush=True)
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": f"Grok API returned {e.code}",
                "detail": err_body.decode(errors="replace")[:300],
            }).encode())
            return
        except Exception as e:
            print(f"[grok-tts-proxy] Upstream error: {e}", flush=True)
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(audio_bytes)))
        self.end_headers()
        self.wfile.write(audio_bytes)


if __name__ == "__main__":
    if not XAI_API_KEY:
        print("ERROR: XAI_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    server = HTTPServer(("0.0.0.0", PORT), GrokTTSHandler)
    print(f"[grok-tts-proxy] Listening on 0.0.0.0:{PORT}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("[grok-tts-proxy] Shutting down", flush=True)
