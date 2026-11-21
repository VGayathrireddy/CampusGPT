
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from retriever import retrieve_relevant_chunks
from llm import generate_answer


# Create FastAPI application
app = FastAPI(
    title="CampusGPT API",
    description="AI-powered college information assistant",
    version="1.0.0"
)


# Allow React frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request format
class ChatRequest(BaseModel):
    question: str


# Response format for PDF and website citations
class Source(BaseModel):
    source_type: str
    document: str
    page: int | None = None
    title: str | None = None
    url: str | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]


# Home endpoint
@app.get("/")
def home():
    return {
        "message": "Welcome to CampusGPT API",
        "status": "running"
    }


# Chat endpoint
@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Please enter a question."
        )

    try:
        # Retrieve relevant chunks from PDFs and website
        chunks = retrieve_relevant_chunks(question)

        # Generate answer using Mistral
        answer = generate_answer(question, chunks)

        # Prepare source citations
        sources = []
        seen_sources = set()

        for chunk in chunks:

            source_type = chunk.get("source_type", "pdf")

            if source_type == "website":

                source_url = chunk.get("url", "")

                source_key = ("website", source_url)

                if source_key not in seen_sources:
                    seen_sources.add(source_key)

                    sources.append({
                        "source_type": "website",
                        "document": chunk.get("title", "Website page"),
                        "page": None,
                        "title": chunk.get("title", ""),
                        "url": source_url
                    })

            else:

                document = chunk.get("source", "")
                page_number = chunk.get("page_number")

                source_key = ("pdf", document, page_number)

                if source_key not in seen_sources:
                    seen_sources.add(source_key)

                    sources.append({
                        "source_type": "pdf",
                        "document": document,
                        "page": page_number,
                        "title": document,
                        "url": None
                    })

        return {
            "answer": answer,
            "sources": sources
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )
