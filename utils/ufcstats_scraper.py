import requests
from bs4 import BeautifulSoup

def fetch_ufcstats(fighter_id):
    url = f"https://www.ufcstats.com/fighter-details/{fighter_id}"

    try:
        html = requests.get(url, timeout=10).text
    except:
        return {}

    soup = BeautifulSoup(html, "html.parser")
    stats = {}

    items = soup.select(".b-list__info-list-item")

    for item in items:
        text = item.get_text(strip=True)
        if "Height:" in text:
            stats["height"] = text.split(":")[-1].strip()
        if "Reach:" in text:
            stats["reach"] = text.split(":")[-1].strip()
        if "DOB:" in text:
            stats["dob"] = text.split(":")[-1].strip()

    return stats
