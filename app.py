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

load_dotenv()  # reads the API key from .env (never commit .env to GitHub)

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
    Hint: collection.query(query_texts=[question], n_results=k)
    Extra: try different k values and note which gives the best answers (for the slides).
    """
    
def retrieve(question: str, collection, k: int = TOP_K) -> list[dict]:
    """Return the k chunks most similar to the question.

    Return [{"source": "week1.pdf", "text": "..."}, ...]
    """

    # Search ChromaDB for the most relevant chunks
    results = collection.query(
        query_texts=[question],
        n_results=k
    )

    # Prepare an empty list to store retrieved chunks
    retrieved_chunks = []

    # Extract documents and their metadata
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]

    # Combine each document with its source filename
    for text, metadata in zip(documents, metadatas):
        retrieved_chunks.append({
            "source": metadata["source"],
            "text": text
        })

    # Return the retrieved chunks
    return retrieved_chunks



# ===========================================================================
# SECTION 3 - MADALITSO: answer generation and wiring
# ===========================================================================
def build_prompt(question: str, chunks: list[dict]) -> str:
    """Build the prompt: instructions + retrieved chunks + the question.

    The instructions must say: answer ONLY from the context, and say
    "I could not find this in the notes" if the answer is not there.
    """
    # TODO (Madalitso)
    raise NotImplementedError


def call_llm(prompt: str) -> str:
    """Send the prompt to Gemini and return the text reply."""
    # TODO (Madalitso): read the key with os.getenv("GEMINI_API_KEY"), call the API
    raise NotImplementedError


def answer_question(question: str, collection) -> dict:
    """The main function the front end calls.

    Return {"answer": "...", "sources": ["week1.pdf", "week3.pdf"]}
    """
    # TODO (Madalitso): retrieve -> build_prompt -> call_llm -> package the result
    raise NotImplementedError


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
    # TODO (Nathan N): st.file_uploader, save to NOTES_FOLDER, then clear the cache
    pass


# NATHAN N: also add error messages and a loading spinner (st.spinner)
# around answer_question, e.g. inside show_chat (agree the details with Wesley).


def main():
    st.title("Course Notes Assistant")
    st.caption("Ask a question. Answers come only from our notes.")
    collection = get_collection()
    show_chat(collection)
    show_upload()


if __name__ == "__main__":
    main()
