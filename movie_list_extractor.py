import os
import time
import json
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, jsonify

# --- CONFIG ---
CACHE_FILE = "movie_cache.json"
CACHE_EXPIRY = 86400  # 24 hours in seconds
TARGET_URL = "https://www.5movierulz.florist/category/malayalam-featured"

def get_movies_from_web():
    """The original scraping logic."""
    print("🌐 [extractor] Cache expired or missing. Scraping web...")
    movies = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36..."}
    
    try:
        resp = requests.get(TARGET_URL, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        items = soup.select('div.content.home_style ul li')
        
        for item in items:
            link = item.find('a')
            if not link: continue
            img = item.find('img')
            
            movies.append({
                "title": link.get('title', 'Untitled').split('(')[0].strip(),
                "url": link.get('href'),
                "thumbnail": img.get('src') if img else ""
            })
            
        # Save to cache file with timestamp
        cache_data = {
            "timestamp": time.time(),
            "movies": movies
        }
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache_data, f)
            
    except Exception as e:
        print(f"[extractor] Scraping failed: {e}")
    
    return movies

def get_cached_movies():
    """Checks if valid cache exists, otherwise triggers scrape."""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            cache_data = json.load(f)
            
        file_age = time.time() - cache_data.get("timestamp", 0)
        
        if file_age < CACHE_EXPIRY:
            print(f"📁 [extractor] Loading from cache (Age: {int(file_age/3600)}h)")
            return cache_data.get("movies", [])
            
    return get_movies_from_web()