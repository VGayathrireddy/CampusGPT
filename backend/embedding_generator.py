
from pathlib import Path
from sentence_transformers import SentenceTransformer
from text_chunker import chunk_pages
from pdf_extractor import extract_text_from_pdf


def generate_embeddings(chunks: list[dict]) -> list[dict]:
    """
    Generate numerical embeddings for text chunks.
    """

    model = SentenceTransformer("all-MiniLM-L6-v2")

    texts = [chunk["text"] for chunk in chunks]

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        show_progress_bar=True
    )

    embedded_chunks = []

    for chunk, embedding in zip(chunks, embeddings):
        embedded_chunks.append({
            "page_number": chunk["page_number"],
            "text": chunk["text"],
            "embedding": embedding
        })

    return embedded_chunks


if __name__ == "__main__":

    project_root = Path(__file__).resolve().parent.parent

    pdf_file = (
        project_root
        / "documents"
        / "academic_calendar_june-dec_2026.pdf"
    )

    pages = extract_text_from_pdf(pdf_file)
    chunks = chunk_pages(pages)

    embedded_chunks = generate_embeddings(chunks)

    print("\nTotal embeddings generated:", len(embedded_chunks))

    for index, item in enumerate(embedded_chunks, start=1):
        print(f"\nChunk {index}")
        print("Page:", item["page_number"])
        print("Text:", item["text"][:100])
        print("Embedding dimensions:", item["embedding"].shape)
        print("First 5 values:", item["embedding"][:5])
