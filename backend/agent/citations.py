def _format_authors_apa(authors):
    """Smith, J., & Doe, A."""
    if not authors:
        return ""

    def to_last_initial(name):
        parts = name.strip().split()
        if len(parts) < 2:
            return name
        last = parts[-1]
        initials = " ".join(f"{p[0]}." for p in parts[:-1] if p)
        return f"{last}, {initials}"

    formatted = [to_last_initial(a) for a in authors]
    if len(formatted) == 1:
        return formatted[0]
    if len(formatted) == 2:
        return f"{formatted[0]}, & {formatted[1]}"
    return ", ".join(formatted[:-1]) + f", & {formatted[-1]}"


def _format_authors_mla(authors):
    """Smith, John, et al."""
    if not authors:
        return ""
    if len(authors) == 1:
        parts = authors[0].strip().split()
        if len(parts) < 2:
            return authors[0]
        return f"{parts[-1]}, {' '.join(parts[:-1])}"
    parts = authors[0].strip().split()
    first_formatted = f"{parts[-1]}, {' '.join(parts[:-1])}" if len(parts) >= 2 else authors[0]
    if len(authors) == 2:
        return f"{first_formatted}, and {authors[1]}"
    return f"{first_formatted}, et al."


def _format_authors_chicago(authors):
    """Smith, John, and Alice Doe."""
    if not authors:
        return ""
    if len(authors) == 1:
        parts = authors[0].strip().split()
        if len(parts) < 2:
            return authors[0]
        return f"{parts[-1]}, {' '.join(parts[:-1])}"
    parts = authors[0].strip().split()
    first_formatted = f"{parts[-1]}, {' '.join(parts[:-1])}" if len(parts) >= 2 else authors[0]
    rest = authors[1:]
    if len(rest) == 1:
        return f"{first_formatted}, and {rest[0]}"
    return f"{first_formatted}, {', '.join(rest[:-1])}, and {rest[-1]}"


def generate_citations(source):
    """Given a source dict with raw_title, authors, year, venue, link -
    return deterministic APA/MLA/Chicago citation strings. No LLM involved,
    since citation formatting must be exact, not AI-approximated."""
    title = source.get("raw_title") or source.get("title") or "Untitled"
    authors = source.get("authors") or []
    year = source.get("year")
    venue = source.get("venue") or ""
    link = source.get("link") or ""
    year_str = str(year) if year else "n.d."

    apa_authors = _format_authors_apa(authors)
    apa = f"{apa_authors} ({year_str}). {title}."
    if venue:
        apa += f" {venue}."
    if link:
        apa += f" {link}"

    mla_authors = _format_authors_mla(authors)
    mla = f'{mla_authors}. "{title}."'
    if venue:
        mla += f" {venue},"
    mla += f" {year_str}"
    if link:
        mla += f", {link}."
    else:
        mla += "."

    chicago_authors = _format_authors_chicago(authors)
    chicago = f'{chicago_authors}. "{title}."'
    if venue:
        chicago += f" {venue}"
    chicago += f" ({year_str})."
    if link:
        chicago += f" {link}."

    return {
        "apa": apa.strip(),
        "mla": mla.strip(),
        "chicago": chicago.strip(),
    }
