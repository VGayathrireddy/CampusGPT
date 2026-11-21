
from pathlib import Path
import chromadb


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATABASE_PATH = PROJECT_ROOT / "data" / "chroma_db"

client = chromadb.PersistentClient(
    path=str(DATABASE_PATH)
)

collection = client.get_or_create_collection(
    name="campus_documents",
    metadata={"hnsw:space": "cosine"}
)


def store_embeddings(embedded_chunks: list[dict], source_name: str):
    """
    Store text chunks, embeddings and metadata in ChromaDB.
    """

    if not embedded_chunks:
        print("No chunks available to store.")
        return

    ids = []
    documents = []
    embeddings = []
    metadatas = []

    for index, item in enumerate(embedded_chunks):

        ids.append(f"{source_name}_page{item['page_number']}_chunk{index + 1}")

        documents.append(item["text"])

        embeddings.append(item["embedding"].tolist())

        metadatas.append({
            "source": source_name,
            "page_number": item["page_number"]
        })

    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )

    print(f"Successfully stored {len(ids)} chunks in ChromaDB.")


if __name__ == "__main__":

    from pdf_extractor import extract_text_from_pdf
    from text_chunker import chunk_pages
    from embedding_generator import generate_embeddings

    pdf_file = (
        PROJECT_ROOT
        / "documents"
        / "academic_calendar_june-dec_2026.pdf"
    )

    pages = extract_text_from_pdf(pdf_file)

    chunks = chunk_pages(pages)

    embedded_chunks = generate_embeddings(chunks)

    store_embeddings(
        embedded_chunks,
        pdf_file.name
    )

    print("Total records in database:", collection.count())
