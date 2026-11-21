
import json
import hashlib
from pathlib import Path

from sentence_transformers import SentenceTransformer
from vector_store import collection


PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = PROJECT_ROOT / "data" / "website_chunks.json"

MODEL_NAME = "all-MiniLM-L6-v2"
BATCH_SIZE = 64


def generate_record_id(url: str, chunk_index: int) -> str:
    """Generate a stable, unique ID for each website chunk."""

    url_hash = hashlib.sha1(
        url.encode("utf-8")
    ).hexdigest()[:16]

    return f"website_{url_hash}_{chunk_index}"


def store_website_chunks():

    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        chunks = json.load(file)

    if not chunks:
        print("No website chunks found.")
        return

    print("Loading embedding model...")
    model = SentenceTransformer(MODEL_NAME)

    print("\nGenerating embeddings and storing website chunks...")

    total_chunks = len(chunks)

    for start in range(0, total_chunks, BATCH_SIZE):

        batch = chunks[start:start + BATCH_SIZE]

        documents = [
            item["text"] for item in batch
        ]

        embeddings = model.encode(
            documents,
            convert_to_numpy=True,
            show_progress_bar=False
        ).tolist()

        ids = []
        metadatas = []

        for item in batch:

            ids.append(
                generate_record_id(
                    item["url"],
                    item["chunk_index"]
                )
            )

            metadatas.append({
                "source_type": "website",
                "title": item["title"],
                "source_url": item["url"],
                "chunk_index": item["chunk_index"]
            })

        collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )

        print(
            f"Stored {min(start + len(batch), total_chunks)}"
            f" / {total_chunks} chunks"
        )

    print("\nWebsite ingestion completed!")
    print("Website chunks processed:", total_chunks)
    print("Total records in ChromaDB:", collection.count())


if __name__ == "__main__":
    store_website_chunks()
