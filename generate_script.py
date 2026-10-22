import json, os, random, re, urllib.request, urllib.error, time
from pathlib import Path

ideas = [
    'Monkey influencer discovers his selfie camera is on during a serious meeting',
    'Monkey influencer tries a viral dance but keeps making ridiculous faces',
    'Monkey influencer pretends to be a millionaire while eating a banana',
    'Monkey influencer reacts dramatically to seeing his own reflection',
    'Monkey influencer gives hilariously bad gym advice',
    'Monkey influencer attempts to look mysterious but sneezes'
]
idea = random.choice(ideas)
prompt = f'''Write a funny 18-25 second short-form comedy narration about: {idea}.
The star is a fictional goofy chimpanzee influencer. Fast hook, visual reaction beats, punchline.
Return ONLY valid JSON with keys: title (string), narration (45-60 words), caption (string), search_queries (array of five strings).
No copyrighted song lyrics, no real-person impersonation, no markdown. Keep family friendly.'''
key = os.environ['OPENROUTER_API_KEY']
payload = {'model':'openrouter/free','messages':[{'role':'user','content':prompt}], 'temperature':0.8}
for attempt in range(3):
    req = urllib.request.Request('https://openrouter.ai/api/v1/chat/completions', data=json.dumps(payload).encode(), headers={'Authorization':f'Bearer {key}','Content-Type':'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            result = json.load(response)
        break
    except urllib.error.HTTPError as exc:
        msg = exc.read().decode(errors='replace')
        if exc.code in (429,500,502,503,504) and attempt < 2:
            time.sleep(5 * (attempt + 1)); continue
        raise RuntimeError(f'OpenRouter error {exc.code}: {msg[:500]}') from exc
content = result['choices'][0]['message']['content'].strip()
content = re.sub(r'^```(?:json)?\s*|\s*```$', '', content).strip()
script = json.loads(content)
if not all(isinstance(script.get(k), str) and script[k].strip() for k in ('title','narration','caption')):
    raise ValueError('Invalid text fields in generated script')
if not isinstance(script.get('search_queries'), list):
    script['search_queries'] = []
Path('output').mkdir(exist_ok=True)
Path('output/script.json').write_text(json.dumps(script, ensure_ascii=False, indent=2), encoding='utf-8')
print('Generated:', script['title'])




