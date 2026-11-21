
import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = PROJECT_ROOT / "data" / "website_pages.json"
OUTPUT_FILE = PROJECT_ROOT / "data" / "cleaned_website_pages.json"


def clean_text(text: str) -> str:
    """Remove unnecessary whitespace from extracted website text."""

    text = re.sub(r"\s+", " ", text)
    return text.strip()


def prepare_website_data():

    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        pages = json.load(file)

    cleaned_pages = []
    seen_urls = set()

    for page in pages:

        url = page.get("url", "").strip()

        # Skip records without a URL
        if not url:
            continue

        # Skip duplicate URLs
        if url in seen_urls:
            continue

        seen_urls.add(url)

        # Sitemap is useful for discovering links, not answering questions
        if "sitemap" in url.lower():
            continue

        title = page.get("title", "").strip()
        text = clean_text(page.get("text", ""))

        # Skip pages with insufficient content
        if len(text) < 200:
            continue

        cleaned_pages.append({
            "title": title,
            "url": url,
            "text": text,
            "crawled_at": page.get("crawled_at", "")
        })

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(
            cleaned_pages,
            file,
            indent=4,
            ensure_ascii=False
        )

    print("\nWebsite Data Preparation Completed!")
    print("-----------------------------------")
    print("Original records:", len(pages))
    print("Unique URLs:", len(seen_urls))
    print("Cleaned records:", len(cleaned_pages))
    print("Removed records:", len(pages) - len(cleaned_pages))
    print("Output file:", OUTPUT_FILE)


if __name__ == "__main__":
    prepare_website_data()
