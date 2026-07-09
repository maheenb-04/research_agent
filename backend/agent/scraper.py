import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

REMOVAL_PHRASES = [
    "has been removed",
    "no longer available",
    "has been withdrawn",
    "paper has been removed",
    "under review or has been removed",
    "page not found",
    "content unavailable",
    "access denied",
    "this content is not available",
    "article not found",
    "post not found",
    "we couldn't find",
    "we could not find",
    "doesn't exist",
    "does not exist",
    "404 error",
    "404 not found",
    "sorry, this page",
    "oops",
    "nothing found",
]

# URL path fragments that strongly indicate a redirect landed on an error page,
# even when the server still responds with HTTP 200 (common on JS-rendered
# single-page apps, where the actual "not found" message is only rendered
# client-side and never appears in the raw HTML our backend sees)
NOT_FOUND_PATH_HINTS = ["/404", "/not-found", "/notfound", "/error"]


def is_link_accessible(url, timeout=6):
    """Check that a source link actually resolves to real, available content -
    not just that the search API returned a URL for it. Some indexed papers
    get pulled after the fact (removed, withdrawn, under review), and the API
    doesn't always know that.

    Known limitation: some sites are JavaScript-rendered single-page apps
    where the "not found" message only appears after client-side rendering -
    it's never present in the raw HTML this function sees, and the server
    still responds 200 OK. This function catches classic server-rendered
    error pages and obvious redirect-to-error-page patterns, but cannot
    reliably catch every JS-rendered soft-404. Fully solving that would
    require a headless browser (e.g. Playwright) to actually render the page,
    which is a heavier dependency than this project currently uses."""
    if not url:
        return False
    try:
        res = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=timeout,
            stream=True,
            allow_redirects=True,
        )
        if res.status_code >= 400:
            return False

        final_url = (res.url or "").lower()
        if any(hint in final_url for hint in NOT_FOUND_PATH_HINTS):
            return False

        chunk = next(res.iter_content(chunk_size=8000, decode_unicode=True), "") or ""
        lowered = chunk.lower()
        if any(phrase in lowered for phrase in REMOVAL_PHRASES):
            return False

        return True
    except Exception:
        return False


def validate_links(entries, target_count, timeout=6, max_workers=10):
    """Validate candidate sources concurrently and return the first
    target_count that are actually accessible, preserving original order."""
    import concurrent.futures

    if not entries:
        return []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_entry = {
            executor.submit(is_link_accessible, e["link"], timeout): e
            for e in entries
        }
        valid_flags = {}
        for future in concurrent.futures.as_completed(future_to_entry):
            entry = future_to_entry[future]
            try:
                valid_flags[id(entry)] = future.result()
            except Exception:
                valid_flags[id(entry)] = False

    validated = [e for e in entries if valid_flags.get(id(e))]
    return validated[:target_count]


def search(topic):
    import requests
    import time
    import re

    MIN_YEAR = 2020
    TARGET_COUNT = 25
    CANDIDATE_POOL = 40

    def try_semantic_scholar():
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            "query": topic,
            "limit": CANDIDATE_POOL,
            "fields": "title,abstract,url,year,authors,venue",
            "year": f"{MIN_YEAR}-"
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
                raw_title = paper.get("title") or "Untitled"
                link = paper.get("url") or ""
                year = paper.get("year")
                abstract = paper.get("abstract") or ""
                authors = [a.get("name") for a in (paper.get("authors") or []) if a.get("name")]
                venue = paper.get("venue") or ""

                if year and year < MIN_YEAR:
                    continue
                if not link:
                    continue

                entry = {
                    "title": f"{raw_title} ({year})" if year else raw_title,
                    "raw_title": raw_title,
                    "link": link,
                    "abstract": abstract,
                    "year": year,
                    "authors": authors,
                    "venue": venue,
                }
                if year and year >= 2025:
                    results.insert(0, entry)
                else:
                    results.append(entry)
            return results
        return None

    def try_crossref():
        url = "https://api.crossref.org/works"
        params = {
            "query": topic,
            "rows": CANDIDATE_POOL,
            "mailto": "research-agent@example.com",
            "filter": f"from-pub-date:{MIN_YEAR}-01-01"
        }
        headers = {"User-Agent": "Mozilla/5.0 (mailto:research-agent@example.com)"}

        res = requests.get(url, params=params, headers=headers, timeout=10)
        res.raise_for_status()
        data = res.json()

        results = []
        for item in data.get("message", {}).get("items", []):
            title_list = item.get("title") or []
            raw_title = title_list[0] if title_list else "Untitled"
            link = item.get("URL") or ""

            year = None
            date_parts = item.get("published", {}).get("date-parts", [[None]])
            if date_parts and date_parts[0]:
                year = date_parts[0][0]

            if year and year < MIN_YEAR:
                continue
            if not link:
                continue

            abstract_raw = item.get("abstract") or ""
            abstract = re.sub(r"<[^>]+>", "", abstract_raw).strip()

            authors = []
            for a in (item.get("author") or []):
                given = a.get("given", "")
                family = a.get("family", "")
                full = (given + " " + family).strip()
                if full:
                    authors.append(full)

            venue_list = item.get("container-title") or []
            venue = venue_list[0] if venue_list else ""

            entry = {
                "title": f"{raw_title} ({year})" if year else raw_title,
                "raw_title": raw_title,
                "link": link,
                "abstract": abstract,
                "year": year,
                "authors": authors,
                "venue": venue,
            }
            if year and year >= 2025:
                results.insert(0, entry)
            else:
                results.append(entry)
        return results

    candidates = None
    try:
        candidates = try_semantic_scholar()
    except Exception:
        candidates = None

    if not candidates:
        try:
            candidates = try_crossref()
        except Exception:
            candidates = []

    return validate_links(candidates or [], TARGET_COUNT)
