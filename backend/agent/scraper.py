import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def search(topic):
    import requests
    import time
    import re

    def try_semantic_scholar():
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            "query": topic,
            "limit": 25,
            "fields": "title,abstract,url,year,authors"
        }
        headers = {"User-Agent": "Mozilla/5.0"}

        for attempt in range(2):
            res = requests.get(url, params=params, headers=headers, timeout=10)
            if res.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            res.raise_for_status()
            data = res.json()

            results = []
            for paper in data.get("data", []):
                title = paper.get("title") or "Untitled"
                link = paper.get("url") or ""
                year = paper.get("year")
                abstract = paper.get("abstract") or ""

                entry = {
                    "title": f"{title} ({year})" if year else title,
                    "link": link,
                    "abstract": abstract
                }
                if year and year >= 2025:
                    results.insert(0, entry)
                else:
                    results.append(entry)
            return results[:25]
        return None  # still rate-limited after retries

    def try_crossref():
        url = "https://api.crossref.org/works"
        params = {
            "query": topic,
            "rows": 25,
            "mailto": "research-agent@example.com"
        }
        headers = {"User-Agent": "Mozilla/5.0 (mailto:research-agent@example.com)"}

        res = requests.get(url, params=params, headers=headers, timeout=10)
        res.raise_for_status()
        data = res.json()

        results = []
        for item in data.get("message", {}).get("items", []):
            title_list = item.get("title") or []
            title = title_list[0] if title_list else "Untitled"
            link = item.get("URL") or ""

            year = None
            date_parts = item.get("published", {}).get("date-parts", [[None]])
            if date_parts and date_parts[0]:
                year = date_parts[0][0]

            abstract_raw = item.get("abstract") or ""
            abstract = re.sub(r"<[^>]+>", "", abstract_raw).strip()

            entry = {
                "title": f"{title} ({year})" if year else title,
                "link": link,
                "abstract": abstract
            }
            if year and year >= 2025:
                results.insert(0, entry)
            else:
                results.append(entry)
        return results[:25]

    try:
        results = try_semantic_scholar()
        if results:
            return results
    except Exception:
        pass

    try:
        return try_crossref()
    except Exception:
        return []
