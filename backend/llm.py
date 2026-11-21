
import ollama
from retriever import retrieve_relevant_chunks


def prepare_context(retrieved_chunks: list[dict]) -> str:
    """
    Organize retrieved chunks by source and document order.
    This helps the model understand information split across chunks.
    """

    grouped_chunks = {}

    for chunk in retrieved_chunks:

        if chunk["source_type"] == "website":
            source_key = chunk.get("url") or chunk.get("title", "Website")

        else:
            source_key = chunk.get("source", "College document")

        if source_key not in grouped_chunks:
            grouped_chunks[source_key] = []

        grouped_chunks[source_key].append(chunk)

    context_parts = []

    for source, chunks in grouped_chunks.items():

        # Restore the original order of chunks from the same source
        chunks.sort(
            key=lambda c: (
                c.get("chunk_index")
                if isinstance(c.get("chunk_index"), int)
                else c.get("page_number") or 0
            )
        )

        first_chunk = chunks[0]

        if first_chunk["source_type"] == "website":

            context_parts.append(
                f"\nSOURCE: {first_chunk.get('title', 'CT University Website')}\n"
                f"URL: {source}\n"
            )

        else:

            context_parts.append(
                f"\nSOURCE: {source}\n"
            )

        for chunk in chunks:

            if chunk["source_type"] == "website":

                context_parts.append(
                    f"\nWebsite chunk {chunk.get('chunk_index')}:\n"
                    f"{chunk['text']}\n"
                )

            else:

                context_parts.append(
                    f"\nPDF page {chunk.get('page_number')}:\n"
                    f"{chunk['text']}\n"
                )

    return "\n".join(context_parts)


def generate_answer(question: str, retrieved_chunks: list[dict]) -> str:
    """
    Generate a grounded answer using the locally running Mistral model.
    """

    if not retrieved_chunks:
        return (
            "I couldn't find this information "
            "in the available college documents."
        )

    context = prepare_context(retrieved_chunks)

    prompt = f"""
You are CampusGPT, an accurate student assistant for CT University.

Answer the student's question using ONLY the supplied source content.

IMPORTANT INSTRUCTIONS:

1. Read all relevant source content before answering.
2. Information in neighbouring chunks may belong to the same course,
   table row, paragraph, or topic.
3. Website fee tables may split course names, eligibility details,
   and fee amounts across multiple chunks. Carefully connect
   consecutive chunks from the same source.
4. Do not confuse regular courses with lateral-entry courses
   or specialized programmes.
5. Associate each fee with the correct course.
6. If a fee or other value is explicitly available, provide it.
7. Do not say information is unavailable when it is present
   in the supplied context.
8. Never guess, calculate, or invent missing information.
9. If the requested information genuinely cannot be established
   from the context, say so clearly.
10. Give a direct, simple answer. Include relevant units and
    distinguish domestic and international fees when available.
11. Do not make up citations or source details.
12. Only include information that directly answers the student's question.
13. Never introduce fees, courses, or facts about unrelated programmes.
14. Never speculate or make comparisons between programmes.
15. If international fees are not clearly associated with the
    requested course, simply omit them.
16. Do not add unnecessary explanations or assumptions.
17. Avoid duplicate programmes, even if their names appear in
    slightly different formats.
18. Present each distinct specialization only once.
19. Separate regular B.Tech programmes from lateral-entry options.
20. Do not list lateral-entry programmes as separate specializations
    unless the student specifically asks about lateral entry.
21. Preserve important distinctions such as IBM collaboration
    and programme specialization.
22. Use a numbered list for multiple programmes.


SOURCE CONTENT:
{context}

STUDENT QUESTION:
{question}

Write the answer clearly and accurately:
"""

    response = ollama.chat(
        model="mistral",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        options={
            "temperature": 0.1
        }
    )

    return response["message"]["content"].strip()


if __name__ == "__main__":

    question = "What is the fee structure for B.Tech CSE?"

    print("\nStudent Question:", question)

    chunks = retrieve_relevant_chunks(question)

    answer = generate_answer(question, chunks)

    print("\nCampusGPT Answer:")
    print(answer)

    print("\nSources:")

    seen_sources = set()

    for chunk in chunks:

        if chunk["source_type"] == "website":
            source = chunk.get("url")

        else:
            source = (
                f"{chunk.get('source')}, "
                f"Page {chunk.get('page_number')}"
            )

        if source and source not in seen_sources:
            seen_sources.add(source)
            print("-", source)
