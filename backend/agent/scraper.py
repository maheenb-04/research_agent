import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def search(topic):
    import requests
    from bs4 import BeautifulSoup

    url = "https://html.duckduckgo.com/html/"
    headers = {"User-Agent": "Mozilla/5.0"}

    res = requests.post(url, data={"q": topic}, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")

    results = []

    for r in soup.find_all("a", class_="result__a"):
        title = r.get_text()
        link = r.get("href")

        # 🔥 prioritize recent content
        if any(x in title.lower() for x in ["2025", "2026", "latest", "new", "breakthrough"]):
            results.insert(0, {"title": title, "link": link})
        else:
            results.append({"title": title, "link": link})

    return results[:5]