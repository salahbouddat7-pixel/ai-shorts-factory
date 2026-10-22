
import json
import os
import random
import re
import time
import urllib.request
import urllib.error
from pathlib import Path

ideas = [
    "Monkey tries a viral dance but keeps making silly faces",
    "Monkey pretends to be rich while eating a banana",
    "Monkey sees himself in the selfie camera and panics",
    "Monkey gives ridiculous gym advice",
    "Monkey tries to act cool but keeps sneezing"
]

idea = random.choice(ideas)

prompt = f"""
Create a funny 20-second Monkey Influencer short about:
{idea}

Return ONLY a valid JSON object with these fields:
"title": string
"narration": string of 45-60 words
"caption": string
"search_queries": array of 5 strings

Use a funny hook, exaggerated facial reactions,
and a strong punchline. Family-friendly comedy.
No markdown.
"""

fallback = {
    "title": "Monkey Tries to Become Famous",
    "narration": (
        "This monkey thinks he's the biggest influencer on the planet. "
        "He starts recording a dance, makes the weirdest face imaginable, "
        "and immediately forgets every single move. "
        "Then he checks his phone, sees one new follower, "
        "and celebrates like he just won a million dollars. "
        "Someone please take away his camera!"
    ),
    "caption": "This monkey needs to be stopped! #FunnyMonkey #Comedy",
    "search_queries": []
}

script = None
key = os.environ.get("OPENROUTER_API_KEY")

if key:
    for attempt in range(3):
        try:
            payload = {
                "model": "openrouter/free",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.5
            }

            request = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json"
                },
                method="POST"
            )

            with urllib.request.urlopen(request, timeout=90) as response:
                result = json.load(response)

            content = result["choices"][0]["message"].get("content") or ""

            # Remove markdown fences.
            content = re.sub(
                r"^```(?:json)?\s*|\s*```$",
                "",
                content.strip()
            ).strip()

            # Extract a JSON object if the model added extra text.
            start = content.find("{")
            end = content.rfind("}")

            if start == -1 or end <= start:
                raise ValueError("No JSON object in AI response")

            candidate = json.loads(content[start:end + 1])

            if not all(
                isinstance(candidate.get(k), str)
                and candidate[k].strip()
                for k in ("title", "narration", "caption")
            ):
                raise ValueError("Missing text fields")

            if not isinstance(candidate.get("search_queries"), list):
                candidate["search_queries"] = []

            script = candidate
            print("AI script generated successfully")
            break

        except (
            urllib.error.HTTPError,
            urllib.error.URLError,
            ValueError,
            KeyError,
            TypeError,
            json.JSONDecodeError
        ) as error:
            print(f"Attempt {attempt + 1} failed: {str(error)[:200]}")
            if attempt < 2:
                time.sleep(5)

if script is None:
    print("Using fallback comedy script")
    script = fallback

Path("output").mkdir(exist_ok=True)

Path("output/script.json").write_text(
    json.dumps(script, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print("Generated:", script["title"])
