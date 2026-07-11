import io
import os
import re
from uuid import uuid4

import streamlit as st
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from supabase import Client, create_client


# --------------------------------------------------
# Configuration
# --------------------------------------------------

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

USER_ID = "vidu"
PDF_BUCKET = "chatbot-pdfs"

st.set_page_config(
    page_title="Advanced PDF AI Chatbot",
    page_icon="🤖",
    layout="wide",
)

st.title("Advanced PDF AI Chatbot")
st.caption("Chat normally or upload a PDF and ask questions about it.")


# --------------------------------------------------
# Validate environment variables
# --------------------------------------------------

if not GROQ_API_KEY:
    st.error("GROQ_API_KEY is missing from the .env file.")
    st.stop()

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("SUPABASE_URL or SUPABASE_KEY is missing from the .env file.")
    st.stop()


# --------------------------------------------------
# Cached online clients and embedding model
# --------------------------------------------------

@st.cache_resource
def get_supabase_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)


@st.cache_resource
def get_groq_model() -> ChatGroq:
    return ChatGroq(
        api_key=GROQ_API_KEY,
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        max_retries=2,
        timeout=60,
    )


@st.cache_resource
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(
        "sentence-transformers/all-MiniLM-L6-v2"
    )


try:
    supabase = get_supabase_client()
    model = get_groq_model()
    embedding_model = get_embedding_model()
except Exception as error:
    st.error(f"Could not initialize the application: {error}")
    st.stop()


# --------------------------------------------------
# Chat history functions
# --------------------------------------------------

def create_conversation(
    user_id: str,
    title: str = "New Chat"
) -> dict:
    """Create a new conversation."""

    response = (
        supabase.table("conversations")
        .insert(
            {
                "user_id": user_id,
                "title": title
            }
        )
        .select("id, title, created_at")
        .execute()
    )

    if not response.data:
        raise RuntimeError("Could not create conversation.")

    return response.data[0]


def load_conversations(user_id: str) -> list[dict]:
    """Load all conversations belonging to the user."""

    response = (
        supabase.table("conversations")
        .select("id, title, created_at, updated_at")
        .eq("user_id", user_id)
        .order("updated_at", desc=True)
        .execute()
    )

    return response.data or []


def load_messages(conversation_id: int) -> list[dict]:
    """Load messages from one selected conversation."""

    response = (
        supabase.table("chat_messages")
        .select("role, content")
        .eq("conversation_id", conversation_id)
        .order("created_at")
        .execute()
    )

    return response.data or []


def save_message(
    user_id: str,
    conversation_id: int,
    role: str,
    content: str
) -> None:
    """Save a message inside one conversation."""

    (
        supabase.table("chat_messages")
        .insert(
            {
                "user_id": user_id,
                "conversation_id": conversation_id,
                "role": role,
                "content": content
            }
        )
        .execute()
    )

    (
        supabase.table("conversations")
        .update({"updated_at": "now()"})
        .eq("id", conversation_id)
        .execute()
    )


def rename_conversation(
    conversation_id: int,
    title: str
) -> None:
    """Rename a conversation."""

    (
        supabase.table("conversations")
        .update({"title": title[:60]})
        .eq("id", conversation_id)
        .execute()
    )


def delete_conversation(conversation_id: int) -> None:
    """Delete a conversation and its messages."""

    (
        supabase.table("conversations")
        .delete()
        .eq("id", conversation_id)
        .execute()
    )

# --------------------------------------------------
# PDF and RAG helper functions
# --------------------------------------------------

def clean_filename(filename: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]", "_", filename)


def extract_pdf_pages(pdf_bytes: bytes) -> list[dict]:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    extracted_pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""

        if text.strip():
            extracted_pages.append(
                {
                    "page_number": page_number,
                    "text": text.strip(),
                }
            )

    return extracted_pages


def split_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 150,
) -> list[str]:
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size.")

    chunks = []
    start = 0
    step = chunk_size - overlap

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += step

    return chunks


def save_pdf_document(
    uploaded_pdf,
    user_id: str,
    conversation_id: int,
) -> dict:
    """Save the original PDF, metadata, chunks, and embeddings."""

    pdf_bytes = uploaded_pdf.getvalue()

    if not pdf_bytes:
        raise ValueError("The uploaded PDF is empty.")

    pages = extract_pdf_pages(pdf_bytes)

    if not pages:
        raise ValueError(
            "No readable text was found. The PDF may contain scanned images."
        )

    safe_name = clean_filename(uploaded_pdf.name)
    storage_path = f"{user_id}/{conversation_id}/{uuid4().hex}_{safe_name}"

    # 1. Save original PDF permanently in Supabase Storage
    supabase.storage.from_(PDF_BUCKET).upload(
        path=storage_path,
        file=pdf_bytes,
        file_options={
            "content-type": "application/pdf",
            "upsert": "false",
        },
    )

    # 2. Save PDF metadata
    response = (
        supabase.table("documents")
        .insert(
            {
                "user_id": user_id,
                "conversation_id": conversation_id,
                "file_name": uploaded_pdf.name,
                "storage_path": storage_path,
            }
        )
        .select("id, conversation_id, file_name, storage_path, created_at")
        .execute()
    )

    if not response.data:
        raise RuntimeError("The PDF metadata could not be saved.")

    document = response.data[0]

    # 3. Create text chunks and embeddings
    chunk_records = []

    for page in pages:
        for chunk in split_text(page["text"]):
            embedding = embedding_model.encode(
                chunk,
                normalize_embeddings=True,
            ).tolist()

            chunk_records.append(
                {
                    "document_id": document["id"],
                    "user_id": user_id,
                    "page_number": page["page_number"],
                    "content": chunk,
                    "embedding": embedding,
                }
            )

    if not chunk_records:
        raise RuntimeError("No searchable PDF chunks were created.")

    # 4. Save chunks in batches
    batch_size = 50

    for index in range(0, len(chunk_records), batch_size):
        batch = chunk_records[index:index + batch_size]

        (
            supabase.table("document_chunks")
            .insert(batch)
            .execute()
        )

    return document


def load_latest_document(
    user_id: str,
    conversation_id: int,
) -> dict | None:
    """Load the latest PDF belonging to one conversation."""

    response = (
        supabase.table("documents")
        .select("id, conversation_id, file_name, storage_path, created_at")
        .eq("user_id", user_id)
        .eq("conversation_id", conversation_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def search_document(
    question: str,
    document_id: int,
    match_count: int = 5,
) -> list[dict]:
    question_embedding = embedding_model.encode(
        question,
        normalize_embeddings=True,
    ).tolist()

    response = supabase.rpc(
        "match_document_chunks",
        {
            "query_embedding": question_embedding,
            "selected_document_id": document_id,
            "match_count": match_count,
        },
    ).execute()

    return response.data or []


def load_all_document_chunks(document_id: int) -> list[dict]:
    """Load all chunks for whole-document questions such as ATS review."""

    response = (
        supabase.table("document_chunks")
        .select("content, page_number")
        .eq("document_id", document_id)
        .order("page_number")
        .execute()
    )

    return response.data or []


def is_whole_document_question(question: str) -> bool:
    """Detect questions that require reviewing the whole resume/PDF."""

    keywords = (
        "ats",
        "resume",
        "cv",
        "percentage",
        "score",
        "friendliness",
        "overall",
        "whole document",
        "entire document",
    )

    normalized = question.lower()
    return any(keyword in normalized for keyword in keywords)


# --------------------------------------------------
# Session state
# --------------------------------------------------

# Load the conversation list
if "conversations" not in st.session_state:
    try:
        st.session_state.conversations = load_conversations(USER_ID)
    except Exception as error:
        st.warning(f"Could not load conversations: {error}")
        st.session_state.conversations = []


# Create the first conversation when none exist
if not st.session_state.conversations:
    try:
        first_conversation = create_conversation(USER_ID)

        st.session_state.conversations = [
            first_conversation
        ]

    except Exception as error:
        st.error(f"Could not create conversation: {error}")
        st.stop()


# Select the newest conversation initially
if "current_conversation_id" not in st.session_state:
    st.session_state.current_conversation_id = (
        st.session_state.conversations[0]["id"]
    )


# Load messages for the selected conversation
if "messages" not in st.session_state:
    try:
        st.session_state.messages = load_messages(
            st.session_state.current_conversation_id
        )
    except Exception as error:
        st.warning(f"Could not load messages: {error}")
        st.session_state.messages = []

if "current_document" not in st.session_state:
    try:
        st.session_state.current_document = load_latest_document(
            USER_ID,
            st.session_state.current_conversation_id,
        )
    except Exception as error:
        st.warning(f"Could not load the previous PDF: {error}")
        st.session_state.current_document = None

if "processed_upload" not in st.session_state:
    st.session_state.processed_upload = None


def switch_conversation(conversation_id: int) -> None:
    """Switch the selected conversation, its messages, and its own PDF."""

    st.session_state.current_conversation_id = conversation_id
    st.session_state.messages = load_messages(conversation_id)
    st.session_state.current_document = load_latest_document(
        USER_ID,
        conversation_id,
    )

    # Do not carry an uploaded file from another conversation.
    st.session_state.processed_upload = None


# --------------------------------------------------
# Sidebar
# --------------------------------------------------

with st.sidebar:
    st.header("Conversations")

    if st.button(
        "➕ New conversation",
        use_container_width=True,
    ):
        try:
            new_conversation = create_conversation(USER_ID)
            st.session_state.conversations = load_conversations(USER_ID)
            switch_conversation(new_conversation["id"])
            st.rerun()
        except Exception as error:
            st.error(f"Could not create conversation: {error}")

    for conversation in st.session_state.conversations:
        conversation_id = conversation["id"]
        conversation_title = conversation["title"]

        is_current = (
            conversation_id
            == st.session_state.current_conversation_id
        )

        button_label = (
            f"▶ {conversation_title}"
            if is_current
            else conversation_title
        )

        if st.button(
            button_label,
            key=f"conversation_{conversation_id}",
            use_container_width=True,
        ):
            try:
                switch_conversation(conversation_id)
                st.rerun()
            except Exception as error:
                st.error(f"Could not switch conversation: {error}")

    st.divider()
    st.header("Document")

    uploader_key = (
        f"rag_pdf_uploader_"
        f"{st.session_state.current_conversation_id}"
    )

    uploaded_pdf = st.file_uploader(
        "Upload a PDF",
        type=["pdf"],
        accept_multiple_files=False,
        key=uploader_key,
    )

    if uploaded_pdf is not None:
        uploaded_key = (
            st.session_state.current_conversation_id,
            uploaded_pdf.name,
            uploaded_pdf.size,
        )

        if st.session_state.processed_upload != uploaded_key:
            try:
                with st.spinner(
                    "Uploading PDF and creating RAG embeddings..."
                ):
                    document = save_pdf_document(
                        uploaded_pdf,
                        USER_ID,
                        st.session_state.current_conversation_id,
                    )

                st.session_state.current_document = document
                st.session_state.processed_upload = uploaded_key
                st.success("PDF saved and processed successfully.")

            except Exception as error:
                st.error(f"Could not process the PDF: {error}")

    if st.session_state.current_document:
        st.info(
            "Current PDF: "
            + st.session_state.current_document["file_name"]
        )
    else:
        st.info("No PDF is connected to this conversation.")

    if st.button(
        "Forget current PDF",
        use_container_width=True,
    ):
        st.session_state.current_document = None
        st.session_state.processed_upload = None
        st.rerun()

    st.divider()

    if st.button(
        "Delete current conversation",
        use_container_width=True,
    ):
        try:
            delete_conversation(
                st.session_state.current_conversation_id
            )

            remaining_conversations = load_conversations(USER_ID)

            if not remaining_conversations:
                remaining_conversations = [
                    create_conversation(USER_ID)
                ]

            st.session_state.conversations = remaining_conversations
            switch_conversation(remaining_conversations[0]["id"])
            st.rerun()

        except Exception as error:
            st.error(f"Could not delete conversation: {error}")


# --------------------------------------------------
# Display conversation
# --------------------------------------------------

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# --------------------------------------------------
# Handle user message
# --------------------------------------------------

user_message = st.chat_input(
    "Ask a question or ask about the uploaded PDF"
)

if user_message:
    user_data = {
        "role": "user",
        "content": user_message,
    }

    st.session_state.messages.append(user_data)

    with st.chat_message("user"):
        st.markdown(user_message)

    try:
        save_message(
            USER_ID,
            st.session_state.current_conversation_id,
            "user",
            user_message,
        )
    except Exception as error:
        st.warning(
            f"Your message could not be saved to Supabase: {error}"
        )

    # Use the first user message as the conversation title.
    if len(st.session_state.messages) == 1:
        conversation_title = user_message.strip()[:40]

        if conversation_title:
            try:
                rename_conversation(
                    st.session_state.current_conversation_id,
                    conversation_title,
                )
                st.session_state.conversations = load_conversations(
                    USER_ID
                )
            except Exception as error:
                st.warning(
                    f"Could not rename conversation: {error}"
                )

    current_document = st.session_state.current_document

    try:
        if current_document:
            # Use recent user messages to make vague follow-up questions
            # such as "what about the percentage?" easier to understand.
            recent_user_messages = [
                message["content"]
                for message in st.session_state.messages[-8:]
                if message["role"] == "user"
            ]

            retrieval_query = " ".join(recent_user_messages)

            whole_document_question = is_whole_document_question(
                user_message
            )

            if whole_document_question:
                relevant_chunks = load_all_document_chunks(
                    current_document["id"]
                )
            else:
                relevant_chunks = search_document(
                    question=retrieval_query,
                    document_id=current_document["id"],
                    match_count=7,
                )

            context_parts = []

            for chunk in relevant_chunks:
                page_number = chunk.get("page_number", "Unknown")
                content = chunk.get("content", "")

                if content:
                    context_parts.append(
                        f"Page {page_number}:\n{content}"
                    )

            document_context = "\n\n".join(context_parts)

            if not document_context:
                document_context = (
                    "No relevant document sections were retrieved."
                )

            system_message = {
                "role": "system",
                "content": f"""
You are a helpful PDF assistant.

Use the recent conversation and the PDF sections below to
understand follow-up questions such as "in here", "the same PDF",
"what about it?", or "that percentage".

Rules:
1. Do not invent facts that are not supported by the PDF.
2. Give a clear and simple answer.
3. Mention page numbers when useful.
4. The current PDF is:
   {current_document["file_name"]}
5. For ATS, resume, or CV questions, review the document as a whole.
6. When the user asks for an ATS percentage or score, you may provide
   a cautious estimated range from 0 to 100 based on structure,
   readability, standard headings, keywords, formatting, and evidence
   in the PDF.
7. Clearly say that the ATS percentage is only an AI estimate and not
   an official score from a real ATS scanner.
8. Never give a score above 100.
9. Explain the main reasons for the estimate and the most important
   improvements.
10. If the PDF genuinely lacks enough readable content, say so clearly.

PDF sections:

{document_context}
""",
            }

        else:
            system_message = {
                "role": "system",
                "content": """
You are a helpful AI assistant.

No PDF is connected to this conversation.
Answer general questions normally.
When the user refers to a document, ask them to upload a PDF
for this conversation.
""",
            }

        groq_messages = [system_message]
        groq_messages.extend(st.session_state.messages[-20:])

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = model.invoke(groq_messages)
                answer = response.content
                st.markdown(answer)

        assistant_data = {
            "role": "assistant",
            "content": answer,
        }

        st.session_state.messages.append(assistant_data)

        try:
            save_message(
                USER_ID,
                st.session_state.current_conversation_id,
                "assistant",
                answer,
            )
        except Exception as error:
            st.warning(
                f"The response could not be saved to Supabase: {error}"
            )

    except Exception as error:
        st.error(
            "The AI request failed. Check the Supabase setup, "
            "internet connection, and API key. "
            f"Details: {error}"
        )