
import os
import json
import time
import urllib.request
import urllib.error

API_KEY = os.environ["OPENROUTER_API_KEY"]
URL = "https://openrouter.ai/api/v1/chat/completions"

prompt = """
Create a 35-second engaging short video script
about 3 terrifying facts about the ocean.

Return ONLY a valid JSON object containing:
{
  "title": "Video title",
  "narration": "75-85 words of factual narration",
  "search_queries": ["query1", "query2", "query3", "query4", "query5"],
  "caption": "Social media caption"
}

Use a strong opening hook. No invented facts.
"""

payload = {
    "model": "openrouter/free",
    "messages": [
        {"role": "user", "content": prompt}
    ],
    "temperature": 0.6
}

for attempt in range(3):
    request = urllib.request.Request(
        URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            result = json.load(response)
        break
    except urllib.error.HTTPError as error:
        details = error.read().decode(
            "utf-8", errors="replace"
        )

        if error.code in (429, 500, 502, 503, 504) and attempt < 2:
            print(f"Temporary API error {error.code}. Retrying...")
            time.sleep(5 * (attempt + 1))
            continue

        print("OpenRouter API status:", error.code)
        print("OpenRouter API error:", details[:1000])
        raise SystemExit(1)

content = result["choices"][0]["message"]["content"].strip()

if content.startswith("```"):
    content = content.split("\n", 1)[1]
    content = content.rsplit("```", 1)[0].strip()

script = json.loads(content)

required = {"title", "narration", "search_queries", "caption"}

if not required.issubset(script):
    raise ValueError("Missing required fields")

if not isinstance(script["search_queries"], list):
    raise ValueError("search_queries must be a list")

os.makedirs("output", exist_ok=True)

with open("output/script.json", "w", encoding="utf-8") as file:
    json.dump(script, file, indent=2, ensure_ascii=False)

print("Script generated successfully!")
print("Title:", script["title"])



