"""
Clean the raw scraped data into a structured knowledge base.

Removes duplicated navigation menus, tokenized code snippets, and
navigation noise. Produces clean, deduplicated, well-structured text
that the RAG retriever can actually use.
"""
import re
from pathlib import Path

RAW = Path("safepay_data.txt")
CLEAN = Path("safepay_knowledge_base.txt")

# --- Noise patterns to strip entirely ---------------------------------------
NOISE_LINES = {
    "", "Login", "Sign Up", "Sign up", "Pricing", "Get started",
    "See pricing", "Start now", "Contact sales", "Sign up today",
    "Explore the docs", "Start with Payments", "Start with Subscriptions",
    "Start with Routing", "Read", "Explore", "Get Started", "Start Here",
    "See Full Reference on Postman", "Inspect the Code in GitHub",
    "Explore Code Samples", "Find a Test Card Number",
    "Build with Safepay", "Start Tutorial", "Learn more",
    "Copy", "Terminal", "Then continue", "setting up your environment",
    "Follow Us on GitHub", "Auto", "Light", "Dark",
}

# Repeated nav-menu block (appears at the top of every scraped page)
NAV_BLOCK = """Products
Products
A single platform to accept payments, protect revenue, and control your finances.
Products
Payments
Accept payments on your website and in-app
Checkout
Supercharged one-click checkout form
Payment Links
Create no-code custom invoices, sharable on any medium
Subscriptions
Recurring payments
Innovation
Payment Orchestration
Route payments to other providers while still using Safepay platform
Offers
Add discount campaigns for your sales and special occasions
Atoms
Tailor your payment experience with advanced UI components
Vault
Tokenization of sensitive data
About
About
Safepay is a regulated PSO/PSP backed by Y Combinator and Stripe and more.
About Safepay
About us
Everything you need to know about Safepay
Careers
Apply for open positions
Contact Sales
Contact the Sales team
Contact Support
Contact our Support team
Legal
Services Agreement
Find all our definations for our services agreement here
Privacy Policy
Peruse our privacy policies
Acceptable Use
Our acceptable use policy and definations
Customer Terms
Please go over our Customer terms
Documentation & resources
Technical Documentation
Explore our integration documents, postman collections and more
Resources
Integration Guide
See our integration documents
API Documentation
Explore our postman collections
Learn
Money Talks
Stay up to date with our latest innovations
Knowledge hub
Have questions? Find out more!"""

# Footer block
FOOTER_BLOCK = """About
About us
Legal
Careers
Contact Sales
Contact Support
Products
Payments
Checkout
Payment Links
Subscriptions
Innovation
Payment Orchestration
Offers
Atoms
Vault
Resources
Integration Guide
API Documentation
Knowledge hub
©
2026
Safepay
021 35622870"""


def clean_text(raw: str) -> str:
    text = raw

    # Remove repeated nav blocks
    text = text.replace(NAV_BLOCK, "")
    text = text.replace(FOOTER_BLOCK, "")

    # Remove "Source:" headers — we'll add our own structure
    text = re.sub(r"Source: https?://\S+", "", text)

    # Remove the tokenized JS code snippet entirely.
    # After scraping, the code is split word-by-word across lines like:
    #   const \n safepay \n = \n require \n ( \n '@sfpy/node-core' \n ) ...
    # We detect the start ("const" followed by "safepay" followed by "require")
    # and the end (the "catch" / "error" / ")" / ";" sequence), then strip it all.
    lines = text.split("\n")
    result_lines = []
    skip = False
    for i, line in enumerate(lines):
        s = line.strip()
        if not skip and s == "const" and i + 2 < len(lines):
            nxt1 = lines[i + 1].strip()
            nxt2 = lines[i + 2].strip()
            if nxt1 == "safepay" and nxt2 in ("=", "require"):
                skip = True
                continue
        if skip:
            # End of code snippet: a line that is just ";" after "error" / ")"
            if s == ";" or (s == "" and any(
                lines[j].strip() == ";" for j in range(max(0, i - 3), i)
            )):
                skip = False
            continue
        result_lines.append(line)
    text = "\n".join(result_lines)

    # Remove standalone number lines (1-16 from code line numbers)
    text = re.sub(r"^\s*\d{1,2}\s*$", "", text, flags=re.MULTILINE)

    # Remove "npx init my-safepay-app" duplicated blocks
    text = re.sub(r"-\s*\n\s*npx\s*\n\s*init my-safepay-app.*?setting up your environment\s*\n\s*\.", "", text, flags=re.DOTALL)

    # Process line by line
    lines = text.split("\n")
    cleaned = []
    seen = set()
    # Additional code-token lines to strip
    CODE_TOKENS = {
        "safepay", "require", "payments", "session", "setup",
        "then", "payment", "=>", "console", "log", "tracker",
        "token", "catch", "error", "authType", "'secret'",
        "host", "'https://api.getsafepay.com'",
        '"merchant_api_key"', '"sec_faed47eb-0044-4968-b7e9-2fb7d7853eb9"',
        '"intent"', '"CYBERSOURCE"', '"mode"', '"payment"',
        '"currency"', '"PKR"', '"amount"', "600000",
        "('@sfpy/node-core')", "('12aslkad23887234234')",
        "{", "}", "(", ")", ";", "=", ".", ",",
        "npx", "init my-safepay-app",
    }
    for line in lines:
        stripped = line.strip()
        if stripped in NOISE_LINES:
            continue
        if stripped in CODE_TOKENS:
            continue
        if stripped in seen:
            continue
        seen.add(stripped)
        cleaned.append(stripped)

    text = "\n".join(cleaned)

    # Collapse 3+ blank lines into 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def main():
    raw = RAW.read_text(encoding="utf-8")
    cleaned = clean_text(raw)

    # Add a clear header
    header = (
        "# SafePay Knowledge Base\n"
        "# Cleaned and structured from getsafepay.com and developer docs.\n"
        "# This is the sole source of truth for the SafePay assistant.\n\n"
    )

    CLEAN.write_text(header + cleaned + "\n", encoding="utf-8")

    raw_lines = len(raw.split("\n"))
    clean_lines = len(cleaned.split("\n"))
    print(f"Raw:   {raw_lines} lines")
    print(f"Clean: {clean_lines} lines")
    print(f"Saved to {CLEAN}")


if __name__ == "__main__":
    main()
