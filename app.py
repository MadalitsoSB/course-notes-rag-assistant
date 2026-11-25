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
load_dotenv()  # reads the API key from .env (never commit .env to GitHub)

# ---------------------------------------------------------------------------
# SETTINGS (shared - agree on changes in the team chat)
# ---------------------------------------------------------------------------
NOTES_FOLDER = "notes"   # put the course notes (.pdf / .txt) here
CHUNK_SIZE = 500         # characters per chunk
CHUNK_OVERLAP = 50       # characters shared between neighbouring chunks
TOP_K = 3                # how many chunks to retrieve per question


# ===========================================================================
# ===========================================================================
# SECTION 1 - ACKSON: load, chunk, embed, store
# ===========================================================================
from pypdf import PdfReader

def load_documents(folder: str) -> list[dict]:
    """Read every .txt and .pdf file in `folder`."""
    documents = []

    # If folder doesn't exist, return empty list so app doesn't crash
    if not os.path.isdir(folder):
        print(f"Folder '{folder}' not found. Create it and add notes.")
        return documents

    for filename in sorted(os.listdir(folder)):
        filepath = os.path.join(folder, filename)
        if not os.path.isfile(filepath):
            continue

        text = ""

        # --- .txt files ---
        if filename.lower().endswith(".txt"):
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()

        # --- .pdf files ---
        elif filename.lower().endswith(".pdf"):
            reader = PdfReader(filepath)
            pages = []
            for page in reader.pages:
                # extract_text() can return None for blank pages
                page_text = page.extract_text() or ""
                pages.append(page_text)
            text = "\n".join(pages)

        else:
            continue  # skip other file types like .docx, .jpg

        text = text.strip()
        if text:  # only keep files that actually have text
            documents.append({"source": filename, "text": text})

    return documents

def split_into_chunks(documents: list[dict]) -> list[dict]:
    """Cut each document into pieces of CHUNK_SIZE characters."""
    chunks = []

    step = CHUNK_SIZE - CHUNK_OVERLAP  # 500 - 50 = 450, so we move 450 each time

    for doc in documents:
        source = doc["source"]
        text = doc["text"]
        chunk_number = 0

        # Slide a window across the text
        for start in range(0, len(text), step):
            end = start + CHUNK_SIZE
            piece = text[start:end].strip()

            if not piece:
                continue

            chunks.append({
                "id": f"{source}-{chunk_number}",
                "source": source,
                "text": piece,
            })
            chunk_number += 1

            # Stop if we reached the end of the document
            if end >= len(text):
                break

    return chunks

def build_vector_store(chunks: list[dict]):
    """Store the chunks in Chroma and return the collection."""
    client = chromadb.Client()

    # Delete old collection if it exists, so we don't get duplicates
    # when we re-run the app
    try:
        client.delete_collection("notes")
    except Exception:
        pass  # it didn't exist yet, that's fine

    collection = client.create_collection("notes")

    if not chunks:
        print("No chunks to store. Add files to notes/ folder.")
        return collection

    collection.add(
        ids=[c["id"] for c in chunks],
        documents=[c["text"] for c in chunks],
        metadatas=[{"source": c["source"]} for c in chunks],
    )
    return collection


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
   
    # Store conversation history between Streamlit reruns
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Question input
    with st.form("chat_form"):
        question = st.text_input(
            "Ask a question about your course notes:",
            placeholder="e.g. What is an operating system?"
        )
        submitted = st.form_submit_button("Ask")

    # Process submitted question
    if submitted:
        if not question.strip():
            st.warning("Please enter a question first.")
        else:
            st.session_state.chat_history.append({
                "role": "user",
                "content": question.strip()
            })

            try:
                with st.spinner("Searching your course notes..."):
                    result = answer_question(question.strip(), collection)

                answer = result["answer"]

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": answer
                })

            except Exception as e:
                st.error(f"Something went wrong: {e}")

    # Display conversation
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])


def show_sources(sources: list[str]):
    """LANZI: show which documents the answer came from (e.g. in an expander)."""
    # TODO (Lanzi)
    pass

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

def main():
    st.title("Course Notes Assistant")
    st.caption("Ask a question. Answers come only from our notes.")
    collection = get_collection()
    show_chat(collection)
    show_upload()

<<<<<<< HEAD
 "sources": []

=======

if __name__ == "__main__":
    main()
>>>>>>> 5e309d9121d4006adff5ff7ad9f067d2bd9a71c0
