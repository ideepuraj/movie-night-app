import os
import time
import json
import requests
from bs4 import BeautifulSoup

# --- CONFIG: update only BASE_URL if the domain changes ---
BASE_URL = "https://www.5movierulz.florist"

CATEGORIES = {
    "malayalam": f"{BASE_URL}/category/malayalam-featured",
    "tamil":     f"{BASE_URL}/category/tamil-featured",
    "hindi":     f"{BASE_URL}/category/bollywood-featured",
    "hollywood": f"{BASE_URL}/category/hollywood-featured",
}

CACHE_DIR    = os.path.join(os.path.dirname(__file__), "cache")
CACHE_EXPIRY = 86400  # 24 hours

os.makedirs(CACHE_DIR, exist_ok=True)

def _cache_file(category, page):
    return os.path.join(CACHE_DIR, f"movie_cache_{category}_p{page}.json")

def _page_url(category, page):
    base = CATEGORIES.get(category)
    if not base:
        return None
    return base if page == 1 else f"{base}/page/{page}"

def get_movies_from_web(category, page=1):
    url = _page_url(category, page)
    if not url:
        print(f"[extractor] Unknown category: {category}")
        return []

    print(f"🌐 [extractor] Scraping {category} page {page}...")
    movies = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36..."}

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        items = soup.select('div.content.home_style ul li')

        for item in items:
            link = item.find('a')
            if not link:
                continue
            img = item.find('img')
            movies.append({
                "title": str(link.get('title') or 'Untitled').split('(')[0].strip(),
                "url": link.get('href'),
                "thumbnail": img.get('src') if img else ""
            })

        cache_data = {"timestamp": time.time(), "movies": movies}
        with open(_cache_file(category, page), 'w') as f:
            json.dump(cache_data, f)

    except Exception as e:
        print(f"[extractor] Scraping failed for {category} page {page}: {e}")

    return movies

def get_cached_movies(category="malayalam", page=1):
    cache_path = _cache_file(category, page)
    if os.path.exists(cache_path):
        with open(cache_path, 'r') as f:
            cache_data = json.load(f)
        file_age = time.time() - cache_data.get("timestamp", 0)
        if file_age < CACHE_EXPIRY:
            print(f"📁 [extractor] {category} p{page} from cache (Age: {int(file_age/3600)}h)")
            return cache_data.get("movies", [])

    return get_movies_from_web(category, page)
