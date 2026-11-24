"""
Course Notes RAG Assistant - BSE2201 team project (SKELETON)

Run:   streamlit run app.py
Setup: pip install -r requirements.txt, then put GEMINI_API_KEY=your-key in a .env file.

THE AGREED CONTRACT (do not change these names or return shapes without telling the team)

    load_documents(folder)                -> list of {"source": str, "text": str}
    split_into_chunks(documents)          -> list of {"id": str, "source": str, "text": str}
    build_vector_store(chunks)            -> a Chroma collection
    retrieve(question, collection, k)     -> list of {"source": str, "text": str}
    answer_question(question, collection) -> {"answer": str, "sources": list[str]}

Work ONLY inside your own section, on your own branch. Replace each TODO and the
`raise NotImplementedError` line.
"""
 
import os

import chromadb
import streamlit as st
from dotenv import load_dotenv
from google import genai

load_dotenv()

# ---------------------------------------------------------------------------
# SETTINGS (shared - agree on changes in the team chat)
# ---------------------------------------------------------------------------
NOTES_FOLDER = "notes"   # put the course notes (.pdf / .txt) here
CHUNK_SIZE = 500         # characters per chunk
CHUNK_OVERLAP = 50       # characters shared between neighbouring chunks
TOP_K = 3                # how many chunks to retrieve per question


# ===========================================================================
# SECTION 1 - ACKSON: load, chunk, embed, store
# ===========================================================================
def load_documents(folder: str) -> list[dict]:
    """Read every .txt and .pdf file in `folder`.

    Return a list like [{"source": "week1.pdf", "text": "full text..."}, ...]
    Hint: use open() for .txt and the `pypdf` library for .pdf.
    """
    # TODO (Ackson)
    raise NotImplementedError


def split_into_chunks(documents: list[dict]) -> list[dict]:
    """Cut each document into pieces of CHUNK_SIZE characters, overlapping by CHUNK_OVERLAP.

    Return [{"id": "week1.pdf-0", "source": "week1.pdf", "text": "..."}, ...]
    """
    # TODO (Ackson)
    raise NotImplementedError


def build_vector_store(chunks: list[dict]):
    """Store the chunks in Chroma and return the collection.

    Hint: chromadb.Client().create_collection("notes") then collection.add(
        ids=[...], documents=[...], metadatas=[{"source": ...}, ...]).
    Chroma creates the embeddings for you with its built-in model.
    """
    # TODO (Ackson)
    raise NotImplementedError


# ===========================================================================
# SECTION 2 - RAPHEAL: retrieval
# ===========================================================================
def retrieve(question: str, collection, k: int = TOP_K) -> list[dict]:
    """Return the k chunks most similar to the question.

    Return [{"source": "week1.pdf", "text": "..."}, ...]
    """
    total = collection.count()
    if total == 0:
        return []

    results = collection.query(
        query_texts=[question],
        n_results=min(k, total)
    )

    retrieved_chunks = []
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]

    for text, metadata in zip(documents, metadatas):
        retrieved_chunks.append({
            "source": metadata["source"],
            "text": text
        })

    return retrieved_chunks

# ===========================================================================
# SECTION 3 - MADALITSO: answer generation and wiring
# ===========================================================================
MODEL = "gemini-flash-latest"

NOT_FOUND = "I could not find this in the notes."


def build_prompt(question: str, chunks: list[dict]) -> str:
    context = "\n\n".join(
        f"[Source: {c['source']}]\n{c['text']}" for c in chunks
    )
    return (
        "You are a course notes assistant. Answer the question using ONLY "
        "the context below. If the answer is not in the context, reply exactly: "
        f"{NOT_FOUND}\n\n"
        f"CONTEXT:\n{context}\n\n"
        f"QUESTION: {question}"
    )


def call_llm(prompt: str) -> str:
    if not os.getenv("GEMINI_API_KEY"):
        return "Error: GEMINI_API_KEY is missing. Add it to your .env file."
    try:
        client = genai.Client()
        response = client.models.generate_content(model=MODEL, contents=prompt)
        return response.text or "The model returned an empty reply."
    except Exception as e:
        return f"Error calling Gemini: {e}"


def answer_question(question: str, collection) -> dict:
    chunks = retrieve(question, collection)
    if not chunks:
        return {"answer": NOT_FOUND, "sources": []}
    answer = call_llm(build_prompt(question, chunks))
    if answer.startswith("Error"):
        return {"answer": answer, "sources": []}
    # If the model says it found nothing, don't list files that didn't help
    if answer.strip().lower().startswith(NOT_FOUND.lower().rstrip(".")):
        return {"answer": answer, "sources": []}
    sources = sorted({c["source"] for c in chunks})
    return {"answer": answer, "sources": sources}

# ===========================================================================
# SECTION 4 - FRONT END (Streamlit)
# ===========================================================================
@st.cache_resource
def get_collection():
    """Build the vector store once and reuse it. (Madalitso connects this.)"""
    docs = load_documents(NOTES_FOLDER)
    chunks = split_into_chunks(docs)
    return build_vector_store(chunks)


def show_chat(collection):
    """WESLEY: chat screen. Question box, a button, and the answer displayed.

    Hint: st.text_input, st.button, st.chat_message. Call answer_question().
    """
    # TODO (Wesley)
    st.info("Chat screen goes here.")


def show_sources(sources: list[str]):
    """LANZI: show which documents the answer came from (e.g. in an expander).

    `sources` is the "sources" list from answer_question(), for example
    ["week1.pdf", "week3.pdf"]. Call this right after showing an answer.
    """
    # Clean the list: skip empty names and repeats (several retrieved chunks
    # often come from the same file), but keep the order they came in.
    unique_sources = []
    for name in sources or []:
        name = str(name).strip()
        if name and name not in unique_sources:
            unique_sources.append(name)

    if not unique_sources:
        st.caption("No sources: this answer did not come from the notes.")
        return

    label = "Source" if len(unique_sources) == 1 else "Sources"
    with st.expander(f"📚 {label} ({len(unique_sources)})"):
        st.caption("This answer was built from these files in the notes folder:")
        for name in unique_sources:
            st.markdown(f"- 📄 `{name}`")

def show_upload():
    """NATHAN N: let the user upload extra notes into the NOTES_FOLDER."""
    uploads = st.file_uploader(
        "Add .txt or .pdf notes", type=["txt", "pdf"], accept_multiple_files=True
    )
    if uploads and st.button("Add to notes"):
        os.makedirs(NOTES_FOLDER, exist_ok=True)
        for f in uploads:
            with open(os.path.join(NOTES_FOLDER, f.name), "wb") as out:
                out.write(f.getbuffer())
        get_collection.clear()
        st.success(f"Added {len(uploads)} file(s). The notes will reload on your next question.")


def answer_with_feedback(question: str, collection) -> dict:
    """NATHAN N: spinner and friendly error message around answer_question."""
    try:
        with st.spinner("Searching the notes..."):
            return answer_question(question, collection)
    except Exception as e:
        st.error(f"Something went wrong while answering: {e}")
        return {"answer": "Sorry, I could not answer that. Please try again.", "sources": []}


, "sources": []}
