# utils/tapology_via_gpt.py
from utils.openai_client import client

def fetch_tapology_data(fighter_name):
    prompt = f"""
Browse Tapology and locate the fighter profile for: {fighter_name}

Extract structured fight history and return JSON list ONLY:
[
  {{
    "result": "",
    "opponent": "",
    "method": "",
    "event": "",
    "round": "",
    "time": "",
    "date": "",
    "promotion": "",
    "weight_class": ""
  }}
]
"""
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return res.choices[0].message.content
