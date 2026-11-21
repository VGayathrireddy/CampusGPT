
from sentence_transformers import SentenceTransformer
from vector_store import collection


# Load the embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Maximum allowed cosine distance
SIMILARITY_THRESHOLD = 0.50

# Number of website candidates to retrieve
WEBSITE_CANDIDATES = 9

# Number of best website matches to expand
MAX_WEBSITE_MATCHES = 5

# Official CT University pages
FEE_PAGE_URL = "https://www.ctuniversity.in/fees"

HOW_TO_APPLY_URL = (
    "https://www.ctuniversity.in/how-to-apply"
)


def search_collection(
    question_embedding: list,
    top_k: int,
    source_filter: dict
) -> list[dict]:
    """Search a specific source type or website page in ChromaDB."""

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=top_k,
        where=source_filter,
        include=["documents", "metadatas", "distances"]
    )

    retrieved_chunks = []

    for document, metadata, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):

        if distance > SIMILARITY_THRESHOLD:
            continue

        retrieved_chunks.append({
            "text": document,
            "source_type": (
                "website"
                if metadata.get("source_type") == "website"
                else "pdf"
            ),
            "source": metadata.get("source", ""),
            "title": metadata.get("title", ""),
            "url": metadata.get("source_url"),
            "page_number": metadata.get("page_number"),
            "chunk_index": metadata.get("chunk_index"),
            "distance": distance
        })

    return retrieved_chunks


def expand_website_chunks(chunks: list[dict]) -> list[dict]:
    """
    Retrieve neighbouring chunks from the same website page.

    This preserves information split across chunk boundaries.
    """

    expanded_chunks = []
    seen_chunks = set()
    page_cache = {}

    for chunk in chunks[:MAX_WEBSITE_MATCHES]:

        url = chunk.get("url")
        chunk_index = chunk.get("chunk_index")

        if not url or not isinstance(chunk_index, int):
            continue

        chunk_key = (url, chunk_index)

        if chunk_key not in seen_chunks:
            seen_chunks.add(chunk_key)
            expanded_chunks.append(chunk)

        # Fetch all chunks from this page only once
        if url not in page_cache:

            page_results = collection.get(
                where={"source_url": url},
                include=["documents", "metadatas"]
            )

            page_chunks = {}

            for document, metadata in zip(
                page_results["documents"],
                page_results["metadatas"]
            ):

                index = metadata.get("chunk_index")

                if isinstance(index, int):
                    page_chunks[index] = {
                        "text": document,
                        "source_type": "website",
                        "source": "",
                        "title": metadata.get("title", ""),
                        "url": url,
                        "page_number": None,
                        "chunk_index": index,
                        "distance": chunk["distance"],
                        "expanded": True
                    }

            page_cache[url] = page_chunks

        # Add previous and next chunks
        page_chunks = page_cache[url]

        for neighbour_index in (
            chunk_index - 1,
            chunk_index + 1
        ):

            neighbour = page_chunks.get(neighbour_index)

            if neighbour:

                neighbour_key = (url, neighbour_index)

                if neighbour_key not in seen_chunks:
                    seen_chunks.add(neighbour_key)
                    expanded_chunks.append(neighbour)

    return expanded_chunks


def retrieve_relevant_chunks(
    question: str,
    top_k: int = 3
) -> list[dict]:
    """
    Retrieval priority:

    1. Search PDF documents first.
    2. For B.Tech CSE eligibility questions, search the
       official fee page directly.
    3. For B.Tech CSE fee questions, use an expanded query.
    4. For general admission-process questions, search the
       official How to Apply page directly.
    5. Otherwise, search general website content.
    6. Expand website results with neighbouring chunks.
    """

    total_records = collection.count()

    if total_records == 0:
        return []

    question_lower = question.lower()

    # Identify B.Tech CSE-related questions
    is_btech_cse = any(
        term in question_lower
        for term in [
            "b.tech",
            "btech",
            "b tech",
            "cse",
            "computer science"
        ]
    )

    # Identify eligibility-related questions
    is_eligibility = any(
        term in question_lower
        for term in [
            "eligibility",
            "eligible",
            "qualification",
            "qualifications",
            "admission criteria",
            "criteria for admission"
        ]
    )

    # Identify fee-related questions
    is_fee_question = any(
        term in question_lower
        for term in [
            "fee",
            "fees",
            "tuition",
            "cost"
        ]
    )

    # Identify general admission-process questions
    is_admission_process = any(
        term in question_lower
        for term in [
            "admission process",
            "admission procedure",
            "application process",
            "how to apply",
            "how can i apply",
            "steps to apply",
            "apply for admission",
            "admission steps"
        ]
    )

    # Avoid routing specialized admission questions
    # to the general admission page.
    is_phd_question = any(
        term in question_lower
        for term in [
            "ph.d",
            "phd",
            "doctoral"
        ]
    )

    is_international_question = any(
        term in question_lower
        for term in [
            "international student",
            "international admission",
            "foreign student"
        ]
    )

    # Improve semantic search for B.Tech CSE fee questions
    retrieval_query = question

    if is_btech_cse and is_fee_question:

        retrieval_query = (
            "B.Tech Computer Science and Engineering "
            "regular course fee per semester"
        )

    question_embedding = model.encode(
        retrieval_query,
        convert_to_numpy=True
    ).tolist()

    # Priority 1: Search PDF documents
    pdf_chunks = search_collection(
        question_embedding,
        top_k,
        {"page_number": {"$gte": 1}}
    )

    if pdf_chunks:
        print("Using PDF documents as the primary source.")
        return pdf_chunks

    # Priority 2: Target official fee page for B.Tech CSE eligibility
    if is_btech_cse and is_eligibility:

        print(
            "Searching the official fee page "
            "for B.Tech CSE eligibility."
        )

        targeted_query = (
            "B.Tech Computer Science and Engineering "
            "regular course eligibility criteria "
            "passed 10+2 examination Physics Mathematics "
            "Chemistry 45 percent marks"
        )

        targeted_embedding = model.encode(
            targeted_query,
            convert_to_numpy=True
        ).tolist()

        targeted_chunks = search_collection(
            targeted_embedding,
            5,
            {"source_url": FEE_PAGE_URL}
        )

        if targeted_chunks:

            print(
                "Found relevant B.Tech CSE eligibility "
                "information on the official fee page."
            )

            expanded_chunks = expand_website_chunks(
                targeted_chunks
            )

            print(
                "Targeted website chunks after expansion:",
                len(expanded_chunks)
            )

            return expanded_chunks

        print(
            "No sufficiently relevant chunks found "
            "on the targeted fee page."
        )

    # Priority 3: Target the official How to Apply page
    # for general admission-process questions.
    if (
        is_admission_process
        and not is_eligibility
        and not is_fee_question
        and not is_phd_question
        and not is_international_question
    ):

        print(
            "Searching the official How to Apply page "
            "for admission-process information."
        )

        targeted_query = (
            "CT University general online and offline "
            "admission process how to apply register "
            "application form dashboard admission office "
            "required documents eligibility verification "
            "fee submission"
        )

        targeted_embedding = model.encode(
            targeted_query,
            convert_to_numpy=True
        ).tolist()

        targeted_chunks = search_collection(
            targeted_embedding,
            5,
            {"source_url": HOW_TO_APPLY_URL}
        )

        if targeted_chunks:

            print(
                "Found admission-process information "
                "on the official How to Apply page."
            )

            expanded_chunks = expand_website_chunks(
                targeted_chunks
            )

            print(
                "Admission website chunks after expansion:",
                len(expanded_chunks)
            )

            return expanded_chunks

        print(
            "No sufficiently relevant chunks found "
            "on the How to Apply page. "
            "Falling back to general website search."
        )

    # Priority 4: General website search
    website_chunks = search_collection(
        question_embedding,
        max(WEBSITE_CANDIDATES, top_k),
        {"source_type": "website"}
    )

    if website_chunks:

        print("No relevant PDF found. Using website sources.")

        expanded_chunks = expand_website_chunks(
            website_chunks
        )

        print(
            "Website chunks after neighbouring-chunk expansion:",
            len(expanded_chunks)
        )

        return expanded_chunks

    return []


if __name__ == "__main__":

    questions = [
        "When do end-semester examinations begin?",
        "What are the hostel facilities available at CT University?",
        "What is the fee structure for B.Tech CSE?",
        "What are the eligibility criteria for B.Tech Computer Science and Engineering?",
        "What is the admission process for B.Tech Computer Science and Engineering at CT University?"
    ]

    for question in questions:

        print("\n" + "=" * 60)
        print("Student Question:", question)

        chunks = retrieve_relevant_chunks(question)

        print("Relevant Chunks Found:", len(chunks))

        for chunk in chunks:

            print("\nSource Type:", chunk["source_type"])
            print("Title:", chunk["title"] or chunk["source"])

            if chunk["source_type"] == "website":
                print("URL:", chunk["url"])
                print("Chunk:", chunk["chunk_index"])
            else:
                print("Page:", chunk["page_number"])

            print("Distance:", round(chunk["distance"], 4))
            print("Text:", chunk["text"][:500])
