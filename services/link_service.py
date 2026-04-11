import re

URL_PATTERN = re.compile(r'https?://[^\s<>"\']+')
MEET_LINK_PATTERN = re.compile(
    r"^https://meet\.google\.com/[a-z]{3}-[a-z]{4}-[a-z]{3}(?:[/?#].*)?$",
    re.IGNORECASE,
)


def extract_links_from_text(raw_text: str) -> list[str]:
    found = URL_PATTERN.findall(raw_text)
    cleaned: list[str] = []
    seen: set[str] = set()

    for url in found:
        url = url.strip().rstrip("),.;")
        if url.lower().startswith("http") and url not in seen:
            cleaned.append(url)
            seen.add(url)

    return cleaned


def analyze_links(raw_text: str) -> tuple[list[str], list[str]]:
    links = extract_links_from_text(raw_text)

    valid_links: list[str] = []
    invalid_links: list[str] = []

    for link in links:
        if MEET_LINK_PATTERN.match(link):
            valid_links.append(link)
        else:
            invalid_links.append(link)

    return valid_links, invalid_links