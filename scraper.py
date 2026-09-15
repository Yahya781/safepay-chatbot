import requests
from bs4 import BeautifulSoup

def scrape_safepay():
    urls = [
        "https://getsafepay.com",
        "https://getsafepay.com/docs",
        "https://getsafepay.com/pricing",
        "https://getsafepay.com/faq",
        "https://safepay-docs.netlify.app/",
    ]
    
    all_text = []
    
    for url in urls:
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Remove scripts and styles
            for tag in soup(["script", "style"]):
                tag.decompose()
            
            text = soup.get_text(separator="\n", strip=True)
            all_text.append(f"Source: {url}\n{text}")
            print(f"Scraped: {url}")
            
        except Exception as e:
            print(f"Failed to scrape {url}: {e}")
    
    return "\n\n".join(all_text)

if __name__ == "__main__":
    content = scrape_safepay()
    with open("safepay_data.txt", "w", encoding="utf-8") as f:
        f.write(content)
    print("Done! Data saved to safepay_data.txt")