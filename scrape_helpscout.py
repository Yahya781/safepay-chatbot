"""
Scrape all Safepay Help Scout documentation articles into a clean knowledge base.

Reads URLs from sitemap_urls.txt, fetches each page, extracts the article body
from <article id="fullArticle">, cleans it, and writes a single clean text file.

Usage: python scrape_helpscout.py
Output: safepay_helpscout_knowledge.txt
"""
import requests
from bs4 import BeautifulSoup
import time
import os

SITEMAP_FILE = "sitemap_urls.txt"
OUTPUT_FILE = "safepay_helpscout_knowledge.txt"

# Only scrape article pages (skip category/collection/home pages which are just indexes)
def is_article(url):
    return "/article/" in url


def clean_text(soup):
    """Extract clean, structured text from an article body."""
    # Remove the print link and any script/style
    for tag in soup(["script", "style", "a.printArticle"]):
        tag.decompose()

    # Remove empty headings
    for h in soup.find_all(["h1", "h2", "h3", "h4"]):
        if not h.get_text(strip=True):
            h.decompose()

    # Convert headings to markdown-style for better chunking
    for h in soup.find_all(["h1", "h2", "h3", "h4"]):
        level = int(h.name[1])
        h.replace_with(f"\n{'#' * level} {h.get_text(strip=True)}\n")

    # Convert list items to bullet points
    for li in soup.find_all("li"):
        li.replace_with(f"- {li.get_text(' ', strip=True)}")

    # Convert paragraphs to plain text with newlines
    for p in soup.find_all("p"):
        p.replace_with(f"{p.get_text(' ', strip=True)}\n")

    # Get remaining text
    text = soup.get_text(separator="\n", strip=True)

    # Clean up excessive blank lines
    lines = [line.strip() for line in text.split("\n")]
    cleaned = []
    prev_blank = False
    for line in lines:
        if not line:
            if not prev_blank:
                cleaned.append("")
            prev_blank = True
        else:
            cleaned.append(line)
            prev_blank = False

    return "\n".join(cleaned)


def scrape_article(url):
    """Fetch and extract clean text from a single article."""
    try:
        response = requests.get(url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SafePay-KB-Scraper"
        })
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        article = soup.find("article", id="fullArticle")

        if not article:
            print(f"  ⚠ No article body found: {url}")
            return None

        title_tag = article.find("h1", class_="title")
        title = title_tag.get_text(strip=True) if title_tag else url.split("/")[-1]

        # Remove the title h1 from the body (we add it separately) to avoid duplication
        if title_tag:
            title_tag.decompose()

        body = clean_text(article)
        return f"## {title}\n{body}"

    except Exception as e:
        print(f"  ✗ Failed: {url} — {e}")
        return None


def main():
    # Load URLs
    if not os.path.exists(SITEMAP_FILE):
        print(f"Error: {SITEMAP_FILE} not found. Run the sitemap fetch first.")
        return

    with open(SITEMAP_FILE, encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]

    articles = [u for u in urls if is_article(u)]
    print(f"Found {len(articles)} article URLs to scrape.\n")

    all_content = []
    success = 0

    for i, url in enumerate(articles, 1):
        print(f"[{i}/{len(articles)}] Scraping: {url.split('/')[-1]}")
        content = scrape_article(url)
        if content:
            all_content.append(content)
            success += 1
        time.sleep(0.5)  # Be polite — small delay between requests

    # Write output
    header = (
        "# Safepay Knowledge Base — Help Scout Documentation\n"
        "# Cleaned and structured from safepay.helpscoutdocs.com\n"
        "# This is the sole source of truth for the SafePay assistant.\n\n"
    )
    full_text = header + "\n\n---\n\n".join(all_content)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(full_text)

    print(f"\n✅ Done! Scraped {success}/{len(articles)} articles.")
    print(f"   Output saved to: {OUTPUT_FILE}")
    print(f"   Total size: {len(full_text):,} characters")


if __name__ == "__main__":
    main()