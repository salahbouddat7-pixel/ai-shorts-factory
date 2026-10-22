import urllib.error
import os
import json
import urllib.request

API_KEY = os.environ["GROQ_API_KEY"]

prompt = """
Create a compelling 35-second YouTube Short about
3 terrifying facts about the ocean.

Return ONLY valid JSON with these fields:
title: a short engaging title
narration: 75-85 words, factually accurate
search_queries: list of 5 short stock footage searches
caption: a social media description

Make the narration interesting from the first
sentence. Avoid fabricated facts.
"""

payload = {
    "model": "llama-3.3-70b-versatile",
    "temperature": 0.7,
    "response_format": {"type": "json_object"},
    "messages": [
        {
            "role": "system",
            "content": "You write factual, engaging short video scripts. Return valid JSON only."
        },
        {
            "role": "user",
            "content": prompt
        }
    ]
}

request = urllib.request.Request(
    "https://api.groq.com/openai/v1/chat/completions",
    data=json.dumps(payload).encode("utf-8"),
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    },
    method="POST"
)

try:
    with urllib.request.urlopen(request, timeout=60) as response:
        result = json.load(response)

except urllib.error.HTTPError as error:
    print("Groq API status:", error.code)
    print("Groq API error:", error.read().decode("utf-8"))
    raise SystemExit(1)

script = json.loads(
    result["choices"][0]["message"]["content"]
)

required = {"title", "narration", "search_queries", "caption"}
if not required.issubset(script):
    raise ValueError("AI response is missing required fields")

os.makedirs("output", exist_ok=True)

with open("output/script.json", "w", encoding="utf-8") as file:
    json.dump(script, file, indent=2, ensure_ascii=False)

print("Generated video title:", script["title"])
print("Narration:", script["narration"])
print("Stock footage searches:", script["search_queries"])
