
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = PROJECT_ROOT / "data" / "cleaned_website_pages.json"
OUTPUT_FILE = PROJECT_ROOT / "data" / "website_chunks.json"

CHUNK_SIZE = 100
CHUNK_OVERLAP = 20


def split_text_into_chunks(text: str) -> list[str]:
    """Split text into word-based chunks with overlap."""

    words = text.split()
    chunks = []

    start = 0

    while start < len(words):

        end = start + CHUNK_SIZE

        chunk_words = words[start:end]
        chunk_text = " ".join(chunk_words)

        if chunk_text.strip():
            chunks.append(chunk_text)

        start += CHUNK_SIZE - CHUNK_OVERLAP

    return chunks


def create_website_chunks():

    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        pages = json.load(file)

    all_chunks = []

    for page in pages:

        title = page["title"]
        url = page["url"]
        text = page["text"]

        chunks = split_text_into_chunks(text)

        for index, chunk in enumerate(chunks, start=1):

            all_chunks.append({
                "title": title,
                "url": url,
                "chunk_index": index,
                "text": chunk
            })

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(
            all_chunks,
            file,
            indent=4,
            ensure_ascii=False
        )

    print("\nWebsite Chunking Completed!")
    print("---------------------------")
    print("Website pages:", len(pages))
    print("Total chunks:", len(all_chunks))
    print("Chunk size:", CHUNK_SIZE, "words")
    print("Chunk overlap:", CHUNK_OVERLAP, "words")
    print("Output file:", OUTPUT_FILE)

    if all_chunks:
        print("\nSample Chunk:")
        print("Title:", all_chunks[0]["title"])
        print("URL:", all_chunks[0]["url"])
        print("Text:", all_chunks[0]["text"][:300])


if __name__ == "__main__":
    create_website_chunks()
