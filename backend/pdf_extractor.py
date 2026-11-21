
from pathlib import Path
import pymupdf


def extract_text_from_pdf(pdf_path: str) -> list[dict]:
    """
    Extract text from a PDF page by page.

    Returns:
        A list containing the page number and extracted text.
    """

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError("The provided file is not a PDF.")

    extracted_pages = []

    with pymupdf.open(pdf_path) as document:

        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text").strip()

            if text:
                extracted_pages.append({
                    "page_number": page_number,
                    "text": text
                })

    return extracted_pages


if __name__ == "__main__":

    project_root = Path(__file__).resolve().parent.parent

    pdf_file = (
        project_root
        / "documents"
        / "academic_calendar_june-dec_2026.pdf"
    )

    pages = extract_text_from_pdf(pdf_file)

    print(f"\nTotal pages containing text: {len(pages)}")

    for page in pages[:2]:
        print(f"\n--- Page {page['page_number']} ---")
        print(page["text"][:1000])
