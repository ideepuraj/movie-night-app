# 🎬 MovieNight

A self-hosted movie night web app that presents a clean browsable UI for your movie list and extracts direct, ad-free HLS video stream URLs from Movierulz pages — so streams can be played directly in VLC, ExoPlayer, or any HLS-compatible player.

> ⚠️ **DISCLAIMER — Please Read**
>
> This project is created **purely for educational and demonstration purposes** to learn about:
> - Web scraping and HTTP request handling
> - HLS (HTTP Live Streaming) protocol internals
> - Reverse engineering of obfuscation techniques (e.g. fake MIME-type headers)
> - Building proxy servers in Python/Flask
>
> The author **does not condone, encourage, or support piracy** in any form.  
> This tool is **not intended** to be used to infringe on any copyright or intellectual property rights.  
> It is the user's sole responsibility to ensure that any content they access complies with applicable laws in their jurisdiction.  
> Always support content creators by using official, licensed platforms.

---

## How It Works

```
Browser (Web UI)
      │
      ▼
 movie_app.py              — Main Flask app (port 8000)
 ├── /                     — Movie list UI
 ├── /api/movies           — Serves cached movie list
 └── /api/extract          — Forwards extraction requests to proxy server
      │
      ▼
 lib/url_proxy_server.py   — Proxy/Extractor server (port 8001, auto-started)
 ├── /api/extract          — Triggers extraction pipeline
 │        │
 │        ▼
 │   lib/url_extractor.py  — Scrapes iframe URLs → yt-dlp → raw .m3u8
 │
 └── /api/proxy            — Transparent HLS proxy that:
                               • Rewrites M3U8 playlist segment URLs
                               • Strips fake PNG headers from .ts video chunks
                               • Attaches required Referer/Origin headers
```

---

## Files

| File | Description |
|------|-------------|
| `movie_app.py` | Main entry point. Flask web app on port 8000. Auto-starts the proxy server and serves the movie list UI. |
| `movie_list_extractor.py` | Builds and caches the list of movies for the UI. |
| `lib/url_extractor.py` | Core extraction logic. Fetches the Movierulz page, finds the embedded player iframe URLs, and uses `yt-dlp` to resolve the raw `.m3u8` stream URL. |
| `lib/url_proxy_server.py` | Flask HTTP server on port 8001 exposing the extraction REST API and the M3U8 proxy. Started automatically by `movie_app.py`. |
| `templates/` | Jinja2 HTML templates for the web UI. |
| `static/` | Static assets (CSS, JS) for the web UI. |
| `requirements.txt` | Python dependencies. |

---

## Setup

### Requirements
- Python 3.9+
- pip
- `yt-dlp` (installed via pip)

### Install

```bash
# Clone the repo
git clone https://github.com/ideepuraj/movie-night-app.git
cd movie-night-app

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate       # Linux/Mac
# .venv\Scripts\activate        # Windows

# Install dependencies
pip install -r requirements.txt
```

### Run

```bash
python movie_app.py
```

This starts both servers automatically:
- **Web UI** → http://localhost:8000
- **Proxy/Extractor** → http://localhost:8001 (internal, auto-started)

Use `APP_PORT` to change the web UI port:

```bash
APP_PORT=9000 python movie_app.py
```

Press **Ctrl+C** to stop — both servers shut down cleanly.

---

## REST API

### `POST /api/extract`

Extract the stream URL from a Movierulz movie page.

**Request:**
```http
POST /api/extract
Content-Type: application/json

{"url": "https://www.5movierulz.viajes/movie-name/movie-watch-online-free-XXXX.html"}
```

**Response (success):**
```json
{
  "success": true,
  "raw_url":   "https://hls2.vcdnx.com/hls/...",
  "proxy_url": "http://localhost:8001/api/proxy?url=..."
}
```

**Response (error):**
```json
{"error": "Could not find embedded player URLs on the page"}
```

> **Use `proxy_url` for playback.** The raw URL requires specific `Referer`/`Origin` HTTP headers that most video players (VLC, ExoPlayer) cannot set. The proxy URL routes through this server which attaches those headers automatically.

### `GET /api/proxy?url=<encoded_url>`

Internal proxy endpoint called by the player. Not meant for direct use — use the `proxy_url` returned from `/api/extract`.

---

## Usage

1. Open **http://localhost:8000** in your browser.
2. Browse your movie list and pick a title.
3. Click a movie to extract its stream URL.
4. Copy the **Proxy URL** to paste into VLC (`Media → Open Network Stream`), or click **▶ Open in VLC** to launch directly.

---

## Raspberry Pi / Remote Access

To run on a Raspberry Pi and access from outside your home network:

```bash
# Install cloudflared for a free HTTPS tunnel (no port forwarding needed)
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64
chmod +x cloudflared-linux-arm64
./cloudflared-linux-arm64 tunnel --url http://localhost:8001
```

This gives you a public URL like `https://xxxx.trycloudflare.com` accessible from anywhere.

---

## Technical Notes

### Why a proxy?
The HLS video host (`vcdnlare.com` / `vcdnx.com`) requires the HTTP `Referer` and `Origin` headers to match their domain. VLC and most native video players cannot set custom headers — so a direct URL would return a 403. The local proxy adds these headers transparently.

### Fake PNG header on `.ts` chunks
The video host prepends a valid 69-byte PNG image to every `.ts` segment to confuse Cloudflare's content scanner. The proxy detects this by looking for the PNG magic bytes (`\x89PNG`) and scans for the real MPEG-TS sync byte (`0x47`) at 188-byte intervals, then strips the fake header before forwarding the clean segment.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

This software is provided "as is" without warranty of any kind. The authors are not responsible for how this software is used.
