
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
    "models/gemini-2.5-flash:generateContent"
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

try:
    with urllib.request.urlopen(request, timeout=90) as response:
        result = json.load(response)
except urllib.error.HTTPError as error:
    print("Gemini API status:", error.code)
    print("Gemini API error:", error.read().decode("utf-8")[:1000])
    raise SystemExit(1)

script = json.loads(
    result["candidates"][0]["content"]["parts"][0]["text"]
)

required = {"title", "narration", "search_queries", "caption"}
if not required.issubset(script):
    raise ValueError("Missing required script fields")

os.makedirs("output", exist_ok=True)

with open("output/script.json", "w", encoding="utf-8") as file:
    json.dump(script, file, indent=2, ensure_ascii=False)

print("Generated video title:", script["title"])
print("Script saved successfully")

