
import json
from pathlib import Path
from collections import Counter


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_FILE = PROJECT_ROOT / "data" / "website_pages.json"


with open(DATA_FILE, "r", encoding="utf-8") as file:
    pages = json.load(file)


print("Total pages:", len(pages))

print("\n--- Website Categories ---")

categories = Counter()

for page in pages:
    path = page["url"].split(".in")[-1]
    category = path.strip("/").split("/")[0] or "homepage"
    categories[category] += 1

for category, count in categories.most_common():
    print(f"{category}: {count}")


print("\n--- Collected Page Details ---")

for index, page in enumerate(pages, start=1):
    print(f"\n{index}. {page['title']}")
    print("URL:", page["url"])
    print("Text length:", len(page["text"]))


print("\n--- Duplicate URL Check ---")

urls = [page["url"] for page in pages]

print("Unique URLs:", len(set(urls)))
print("Duplicate URLs:", len(urls) - len(set(urls)))
