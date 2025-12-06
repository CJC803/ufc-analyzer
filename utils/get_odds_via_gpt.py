import openai

def get_fight_odds(fighter_a, fighter_b):
    prompt = f"""
Search public betting sites for odds for:
{fighter_a} vs {fighter_b}

Prefer:
- BestFightOdds
- OddsShark
- ESPN

Return JSON ONLY:
{
  "fighter_a": "",
  "fighter_b": "",
  "implied_a": 0,
  "implied_b": 0,
  "source": ""
}
"""
    res = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return res["choices"][0]["message"]["content"]
