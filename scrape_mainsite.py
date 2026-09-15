"""
Scrape all Safepay main website pages (safepay.pk / getsafepay.pk) into a clean knowledge base.

The main site is a Next.js app. Each page's content lives in the <main> tag.
Headings, paragraphs, and lists are extracted and converted to markdown.

Usage: python scrape_mainsite.py
Output: safepay_mainsite_knowledge.txt
"""
import requests
from bs4 import BeautifulSoup
import re
import time

SITEMAP_URL = "https://safepay.pk/sitemap.xml"
OUTPUT_FILE = "safepay_mainsite_knowledge.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SafePay-MainSite-Scraper"
}

# Pages to skip (no useful content for the assistant)
SKIP_PATHS = [
    "/login",
    "/signup",
    "/contact/sales",
    "/contact/support",
]


def get_sitemap_urls():
    """Fetch all URLs from the sitemap."""
    r = requests.get(SITEMAP_URL, timeout=20, headers=HEADERS)
    r.raise_for_status()
    urls = re.findall(r"<loc>(.*?)</loc>", r.text)
    return urls


def extract_pricing_pairs(main):
    """Extract 'Feature: Price' pairs from pricing cards.

    The pricing page renders each feature as a <section class="bg-primary-grey">
    card containing exactly two <h4> headings: the feature name and its price.
    Flattening them into separate headings breaks retrieval, so we merge them.
    """
    pairs = []
    for section in main.find_all("section", class_=lambda c: c and "bg-primary-grey" in c):
        h4s = [h.get_text(strip=True) for h in section.find_all("h4")]
        if len(h4s) == 2:
            pairs.append(f"{h4s[0]}: {h4s[1]}")
    return pairs


def extract_content(main):
    """Extract clean, structured markdown-like text from the <main> element."""
    lines = []

    for el in main.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "pre", "tr", "div", "span"]):
        # Skip paragraphs nested inside list items
        if el.name == "p" and el.find_parent("li"):
            continue
        # Skip nested list items
        if el.name == "li" and el.find_parent("li"):
            continue
        # Skip div/span nested inside already-captured text tags
        if el.name in ("div", "span") and el.find_parent(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "pre", "tr"]):
            continue

        if el.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
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

        elif el.name in ("div", "span"):
            # Next.js renders descriptive text in leaf <div>/<span> elements
            # instead of <p> tags. Capture only pure-text leaves (el.string is
            # set only when the element has a single text child), which avoids
            # container divs and button/nav text.
            text = el.string
            if text and text.strip():
                lines.append(text.strip())

    # Clean up excessive blank lines and deduplicate identical lines.
    # The site renders content twice for responsive layouts, so duplicates
    # can be non-consecutive — use a set to remove all exact duplicates.
    cleaned = []
    seen = set()
    prev_blank = False
    for line in lines:
        if not line.strip():
            if not prev_blank:
                cleaned.append("")
            prev_blank = True
        else:
            if line in seen:
                continue
            seen.add(line)
            cleaned.append(line)
            prev_blank = False

    return "\n".join(cleaned)


def scrape_page(url):
    """Fetch and extract clean text from a single page."""
    try:
        response = requests.get(url, timeout=20, headers=HEADERS)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Page title from <title> tag
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else url
        # Clean up title suffix
        title = re.sub(r"\s*[|\-]\s*Safepay.*$", "", title).strip()

        main = soup.find("main")
        if not main:
            print(f"  ⚠ No <main> found: {url}")
            return None

        body = extract_content(main)

        # Merge pricing feature/price pairs so retrieval can associate them
        pricing_pairs = extract_pricing_pairs(main)
        if pricing_pairs:
            pricing_block = "\n".join(f"- {p}" for p in pricing_pairs)
            body = f"{body}\n\n## Pricing\n{pricing_block}"

        if not body.strip():
            print(f"  ⚠ Empty content: {url}")
            return None

        return f"## {title}\n{body}"

    except Exception as e:
        print(f"  ✗ Failed: {url} — {e}")
        return None


def main():
    print(f"Fetching sitemap from {SITEMAP_URL}...")
    urls = get_sitemap_urls()
    print(f"Found {len(urls)} URLs.\n")

    # Filter out skip paths
    pages = [u for u in urls if not any(skip in u for skip in SKIP_PATHS)]
    print(f"Scraping {len(pages)} pages (skipped {len(urls) - len(pages)}).\n")

    all_content = []
    success = 0

    for i, url in enumerate(pages, 1):
        print(f"[{i}/{len(pages)}] Scraping: {url}")
        content = scrape_page(url)
        if content:
            all_content.append(content)
            success += 1
        time.sleep(0.5)

    # Write output
    header = (
        "# Safepay Knowledge Base — Main Website\n"
        "# Cleaned and structured from safepay.pk / getsafepay.pk\n"
        "# This is the sole source of truth for the SafePay assistant.\n\n"
    )
    full_text = header + "\n\n---\n\n".join(all_content)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(full_text)

    print(f"\n✅ Done! Scraped {success}/{len(pages)} pages.")
    print(f"   Output saved to: {OUTPUT_FILE}")
    print(f"   Total size: {len(full_text):,} characters")


if __name__ == "__main__":
    main()