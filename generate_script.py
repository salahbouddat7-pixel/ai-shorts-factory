import time
import random
import os
import json
import urllib.request
import urllib.error

api_key = os.environ["GEMINI_API_KEY"]

prompt = """
Create an engaging 35-second short video about
3 terrifying facts about the ocean.

Return a JSON object containing:
title: engaging video title
narration: 75-85 factual words
search_queries: 5 short stock footage search phrases
caption: social media description

Avoid fabricated facts. Use an attention-grabbing hook.
"""

url = (
    "https://generativelanguage.googleapis.com/v1beta/"
    "models/gemini-3.8-flash:generateContent"
)

payload = {
    "contents": [
        {"parts": [{"text": prompt}]}
    ],
    "generationConfig": {
        "responseMimeType": "application/json"
    }
}

request = urllib.request.Request(
    url,
    data=json.dumps(payload).encode("utf-8"),
    headers={
        "x-goog-api-key": api_key,
        "Content-Type": "application/json"
    },
    method="POST"
)


for attempt in range(5):
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            result = json.load(response)
        break

    except urllib.error.HTTPError as error:
        status = error.code
        details = error.read().decode("utf-8", errors="replace")

        if status in (429, 500, 502, 503, 504) and attempt < 4:
            wait = min(60, 2 ** (attempt + 2)) + random.uniform(0, 2)
            print(f"Gemini temporarily unavailable ({status}). Retrying in {wait:.1f}s...")
            time.sleep(wait)
            continue

        print("Gemini API status:", status)
        print("Gemini API error:", details[:1000])
        raise SystemExit(1)


