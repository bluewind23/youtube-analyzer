# services/youtube_api.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

def search_youtube(query, max_results=20):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "maxResults": max_results,
        "type": "video",
        "key": YOUTUBE_API_KEY
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print("유튜브 검색 실패:", response.text)
        return None
