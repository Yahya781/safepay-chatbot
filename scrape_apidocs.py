"""
Scrape all Safepay API documentation pages (safepay-docs.netlify.app) into a clean knowledge base.

The docs site is a Next.js app with server-rendered content. Each page's main
content lives in a container div (class contains "py-10" and "px-14"), with
headings marked data-heading="true" and paragraphs marked data-text="true".

Usage: python scrape_apidocs.py
Output: safepay_apidocs_knowledge.txt
"""
import requests
from bs4 import BeautifulSoup
import time

BASE_URL = "https://safepay-docs.netlify.app"
OUTPUT_FILE = "safepay_apidocs_knowledge.txt"

# All 16 pages discovered from the homepage navigation
PAGES = [
    "/",
    "/payments/overview",
    "/no-code/overview",
    "/developers/overview",
    "/documentation/introduction",
    "/get-started/overview",
    "/get-started/project-timeline",
    "/get-started/website-checklist",
    "/setup-safepay/create-account/overview",
    "/setup-safepay/operations/settlement-file",
    "/faq",
    "/developers/safepay/sandbox-environment",
    "/build-your-integration/overview",
    "/concepts/tracker",
    "/developers/webhooks/overview",
    "/developers/safepay/test-cards",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SafePay-API-Docs-Scraper"
}


def find_main_container(soup):
    """Locate the main content container div (class contains 'py-10' and 'px-14')."""
    for div in soup.find_all("div"):
        cls = " ".join(div.get("class", []))
        if "py-10" in cls and "px-14" in cls:
            return div
    return None


def extract_content(container):
    """Extract clean, structured markdown-like text from the main content container."""
    lines = []

    # Process content elements in document order, avoiding double-counting
    for el in container.find_all(["h1", "h2", "h3", "h4", "p", "li", "pre", "tr"]):
        # Skip paragraphs nested inside list items (li text already captures them)
        if el.name == "p" and el.find_parent("li"):
            continue
        # Skip nested list items (outer li text already captures them)
        if el.name == "li" and el.find_parent("li"):
            continue
        # Skip table cells (tr text already captures them)
        if el.name in ("td", "th"):
            continue

        if el.name in ("h1", "h2", "h3", "h4"):
            level = int(el.name[1])
            text = el.get_text(strip=True)
            if text:
                lines.append(f"\n{'#' * level} {text}\n")

        elif el.name == "p":
            text = el.get_text(" ", strip=True)
            if text:
                lines.append(text)

        elif el.name == "li":
            text = el.get_text(" ", strip=True)
            if text:
                lines.append(f"- {text}")

        elif el.name == "pre":
            text = el.get_text(strip=True)
            if text:
                lines.append(f"```\n{text}\n```")

        elif el.name == "tr":
            cells = [c.get_text(" ", strip=True) for c in el.find_all(["td", "th"])]
            if cells:
                lines.append(" | ".join(cells))

    # Clean up excessive blank lines and deduplicate consecutive identical lines
    # (the site renders some content twice for responsive layouts)
    cleaned = []
    prev_blank = False
    prev_line = None
    for line in lines:
        if not line.strip():
            if not prev_blank:
                cleaned.append("")
            prev_blank = True
            prev_line = None
        else:
            if line == prev_line:
                continue  # skip consecutive duplicate
            cleaned.append(line)
            prev_blank = False
            prev_line = line

    return "\n".join(cleaned)


def scrape_page(path):
    """Fetch and extract clean text from a single docs page."""
    url = BASE_URL + path
    if not path.endswith("/"):
        url += "/"

    try:
        response = requests.get(url, timeout=20, headers=HEADERS)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Page title from <title> tag
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else path
        # Strip the " - Safepay Documentation" suffix
        title = title.replace(" - Safepay Documentation", "").strip()

        container = find_main_container(soup)
        if not container:
            print(f"  ⚠ No main content container found: {path}")
            return None

        body = extract_content(container)
        if not body.strip():
            print(f"  ⚠ Empty content: {path}")
            return None

        return f"## {title}\n{body}"

    except Exception as e:
        print(f"  ✗ Failed: {path} — {e}")
        return None


def main():
    print(f"Scraping {len(PAGES)} pages from {BASE_URL}\n")

    all_content = []
    success = 0

    for i, path in enumerate(PAGES, 1):
        print(f"[{i}/{len(PAGES)}] Scraping: {path}")
        content = scrape_page(path)
        if content:
            all_content.append(content)
            success += 1
        time.sleep(0.5)  # Be polite — small delay between requests

    # Write output
    header = (
        "# Safepay Knowledge Base — API Documentation\n"
        "# Cleaned and structured from safepay-docs.netlify.app\n"
        "# This is the sole source of truth for the SafePay assistant.\n\n"
    )
    full_text = header + "\n\n---\n\n".join(all_content)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(full_text)

    print(f"\n✅ Done! Scraped {success}/{len(PAGES)} pages.")
    print(f"   Output saved to: {OUTPUT_FILE}")
    print(f"   Total size: {len(full_text):,} characters")


if __name__ == "__main__":
    main()