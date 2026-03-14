import os
import sys
import signal
import requests
import subprocess
import threading
from flask import Flask, render_template, jsonify, request
from movie_list_extractor import get_cached_movies

app_dir = os.getcwd()
proxy_script = os.path.join(app_dir, 'lib', 'url_proxy_server.py')
app = Flask(__name__,
            template_folder=os.path.join(app_dir, 'templates'),
            static_folder=os.path.join(app_dir, 'static'))

proxy_process = None

def start_proxy_server():
    """Launches the lib/url_proxy_server.py on port 8001."""
    global proxy_process
    if os.path.exists(proxy_script):
        print(f"🚀 [System] Starting Proxy/Extractor on port 8001...")
        proxy_process = subprocess.Popen(['python3', proxy_script, "8001"])
    else:
        print(f"❌ [Error] Missing proxy script at: {proxy_script}")

def shutdown(_signum, _frame):
    print("\n👋 [System] Shutting down...")
    if proxy_process and proxy_process.poll() is None:
        proxy_process.terminate()
        proxy_process.wait()
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

# Start the proxy background process
threading.Thread(target=start_proxy_server, daemon=True).start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/movies')
def api_movies():
    # Fetch movie list for the UI
    movies = get_cached_movies()
    return jsonify({"success": True, "movies": movies})

# --- PROXY CONFIG ---
PROXY_URL = "http://localhost:8001/api/extract"

@app.route('/api/extract', methods=['POST'])
def api_extract():
    data = request.get_json()
    movie_url = data.get("url")

    try:
        resp = requests.post(
            f"{PROXY_URL}",
            json={"url": movie_url},
            timeout=20
        )
        return jsonify(resp.json())

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

if __name__ == '__main__':
    app_port = int(os.environ.get("APP_PORT", 8000))
    print("=" * 60)
    print("  MovieNight")
    print("=" * 60)
    print(f"  Web UI:   http://localhost:{app_port}/")
    print("  Press Ctrl+C to stop")
    print("=" * 60)
    app.run(host="0.0.0.0", port=app_port, debug=False)