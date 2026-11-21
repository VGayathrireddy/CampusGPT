
from pathlib import Path
from pdf_extractor import extract_text_from_pdf


def chunk_text(text: str, chunk_size: int = 100, overlap: int = 20) -> list[str]:
    """
    Divide text into smaller chunks using words.
    """

    words = text.split()
    chunks = []

    start = 0

    while start < len(words):
        end = start + chunk_size

        chunk = " ".join(words[start:end])
        chunks.append(chunk)

        if end >= len(words):
            break

        start = end - overlap

    return chunks


def chunk_pages(pages: list[dict]) -> list[dict]:
    """
    Create chunks while preserving page numbers.
    """

    all_chunks = []

    for page in pages:
        page_chunks = chunk_text(page["text"])

        for chunk in page_chunks:
            all_chunks.append({
                "page_number": page["page_number"],
                "text": chunk
            })

    return all_chunks


if __name__ == "__main__":

    project_root = Path(__file__).resolve().parent.parent

    pdf_file = (
        project_root
        / "documents"
        / "academic_calendar_june-dec_2026.pdf"
    )

    pages = extract_text_from_pdf(pdf_file)

    chunks = chunk_pages(pages)

    print("Total pages:", len(pages))
    print("Total chunks:", len(chunks))

    for index, chunk in enumerate(chunks[:3], start=1):
        print(f"\n--- Chunk {index} ---")
        print("Page:", chunk["page_number"])
        print(chunk["text"])
