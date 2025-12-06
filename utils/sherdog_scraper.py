import requests
from bs4 import BeautifulSoup

def fetch_sherdog_profile(url):
    try:
        html = requests.get(url, timeout=10).text
    except:
        return []

    soup = BeautifulSoup(html, "html.parser")
    fights = []

    rows = soup.select(".module.fight_history tr")

    for row in rows:
        cols = [c.get_text(strip=True) for c in row.find_all("td")]
        if len(cols) >= 5:
            fights.append({
                "result": cols[0],
                "opponent": cols[1],
                "method": cols[2],
                "round": cols[3],
                "time": cols[4]
            })
    return fights
