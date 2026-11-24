import os
import uuid
import shutil
from typing import Optional
from flask import Flask, render_template, request, jsonify, session
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

import create_db
import database

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "documind-super-secret-key-prod-2026")
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024  # 32 MB max upload
app.config["UPLOAD_FOLDER"] = os.path.join(os.getcwd(), "uploads")

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
database.init_db()

# LLM Initialization (using user's exact model)
def get_llm():
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY is not configured in environment variables.")
    return ChatGroq(
        model="openai/gpt-oss-120b",
        api_key=groq_api_key,
        temperature=0.2
    )

# Exact Prompt Template from user's RAG pipeline
PROMPT_TEMPLATE = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a helpful AI assistant.

Use ONLY the provided context to answer the question.

If the answer is not present in the context,
say: "I could not find the answer in the document."
"""
        ),
        (
            "human",
            """Context:
{context}

Question:
{question}
"""
        )
    ]
)


def get_current_session_id() -> str:
    """Ensure every visitor gets an isolated session identifier."""
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return session["session_id"]


@app.route("/")
def index():
    session_id = get_current_session_id()
    return render_template("index.html")


@app.route("/documents", methods=["GET"])
def get_documents():
    session_id = get_current_session_id()
    docs = database.get_documents_by_session(session_id)
    active_doc_id = session.get("active_doc_id")
    return jsonify({
        "success": True,
        "documents": docs,
        "active_doc_id": active_doc_id
    })


@app.route("/upload", methods=["POST"])
def upload_pdf():
    session_id = get_current_session_id()

    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "error": "No file selected."}), 400

    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"success": False, "error": "Only PDF files are supported."}), 400

    doc_id = str(uuid.uuid4())
    safe_filename = secure_filename(file.filename) or f"document_{doc_id[:8]}.pdf"
    
    user_upload_dir = os.path.join(app.config["UPLOAD_FOLDER"], session_id)
    os.makedirs(user_upload_dir, exist_ok=True)
    saved_path = os.path.join(user_upload_dir, f"{doc_id}_{safe_filename}")

    try:
        file.save(saved_path)
        file_size = os.path.getsize(saved_path)

        if file_size == 0:
            os.remove(saved_path)
            return jsonify({"success": False, "error": "Uploaded file is empty."}), 400

        # Collection name isolated per user session and document
        collection_name = f"user_{session_id[:8]}_doc_{doc_id[:8]}"

        # Process document through the RAG pipeline
        process_result = create_db.process_pdf(
            pdf_path=saved_path,
            collection_name=collection_name
        )

        # Store document record in SQLite
        database.add_document(
            doc_id=doc_id,
            session_id=session_id,
            filename=safe_filename,
            file_path=saved_path,
            file_size=file_size,
            pages_count=process_result["pages_count"],
            chunks_count=process_result["chunks_count"],
            collection_name=collection_name
        )

        session["active_doc_id"] = doc_id

        return jsonify({
            "success": True,
            "document": {
                "id": doc_id,
                "filename": safe_filename,
                "pages": process_result["pages_count"],
                "chunks": process_result["chunks_count"],
                "file_size": file_size
            }
        })

    except Exception as e:
        if os.path.exists(saved_path):
            try:
                os.remove(saved_path)
            except Exception:
                pass
        return jsonify({"success": False, "error": f"Failed to process document: {str(e)}"}), 500


@app.route("/select-document", methods=["POST"])
def select_document():
    session_id = get_current_session_id()
    data = request.get_json() or {}
    doc_id = data.get("document_id")

    if not doc_id:
        return jsonify({"success": False, "error": "Document ID required."}), 400

    doc = database.get_document_by_id(doc_id, session_id)
    if not doc:
        return jsonify({"success": False, "error": "Document not found."}), 404

    session["active_doc_id"] = doc_id
    return jsonify({"success": True, "active_doc_id": doc_id, "filename": doc["filename"]})


@app.route("/delete-document", methods=["POST"])
def delete_document():
    session_id = get_current_session_id()
    data = request.get_json() or {}
    doc_id = data.get("document_id") or session.get("active_doc_id")

    if not doc_id:
        return jsonify({"success": False, "error": "Document ID is required."}), 400

    doc = database.delete_document_record(doc_id, session_id)
    if not doc:
        return jsonify({"success": False, "error": "Document not found."}), 404

    # Delete Chroma collection
    create_db.delete_document_collection(doc["collection_name"])

    # Delete physical file from uploads
    if os.path.exists(doc["file_path"]):
        try:
            os.remove(doc["file_path"])
        except Exception as e:
            print(f"Warning: Failed to delete file {doc['file_path']}: {e}")

    if session.get("active_doc_id") == doc_id:
        # Switch to another available document or None
        remaining = database.get_documents_by_session(session_id)
        session["active_doc_id"] = remaining[0]["id"] if remaining else None

    return jsonify({
        "success": True,
        "message": f"Document '{doc['filename']}' deleted successfully.",
        "active_doc_id": session.get("active_doc_id")
    })


@app.route("/chat", methods=["POST"])
def chat():
    session_id = get_current_session_id()
    data = request.get_json() or {}
    query = (data.get("message") or "").strip()
    conversation_id = data.get("conversation_id")
    doc_id = data.get("document_id") or session.get("active_doc_id")

    if not query:
        return jsonify({"success": False, "error": "Question cannot be empty."}), 400

    # Ensure user has selected or uploaded a document
    if not doc_id:
        docs = database.get_documents_by_session(session_id)
        if docs:
            doc_id = docs[0]["id"]
            session["active_doc_id"] = doc_id
        else:
            return jsonify({
                "success": False,
                "error": "No document uploaded. Please upload a PDF document first."
            }), 400

    doc = database.get_document_by_id(doc_id, session_id)
    if not doc:
        return jsonify({"success": False, "error": "Selected document was not found."}), 404

    # Create or continue conversation
    conv_id = database.get_or_create_conversation(conversation_id, session_id, first_message=query)

    try:
        # Initialize MMR Retriever for the specific document
        retriever = create_db.get_document_retriever(
            collection_name=doc["collection_name"],
            k=4,
            fetch_k=10,
            lambda_mult=0.5
        )

        retrieved_docs = retriever.invoke(query)

        # Build context from retrieved chunks
        context = "\n\n".join([d.page_content for d in retrieved_docs])

        # Prepare sources for transparency
        sources = []
        for d in retrieved_docs:
            sources.append({
                "page": d.metadata.get("display_page", d.metadata.get("page", 0) + 1 if "page" in d.metadata else 1),
                "document": doc["filename"],
                "snippet": d.page_content[:180].strip() + ("..." if len(d.page_content) > 180 else "")
            })

        # Format prompt and invoke Groq LLM
        llm = get_llm()
        final_prompt = PROMPT_TEMPLATE.invoke({
            "context": context if context else "No relevant context found.",
            "question": query
        })
        ai_response = llm.invoke(final_prompt)
        answer_text = ai_response.content

        # Save to database
        database.add_message(conv_id, session_id, role="user", content=query)
        database.add_message(conv_id, session_id, role="assistant", content=answer_text, sources=sources)

        return jsonify({
            "success": True,
            "response": answer_text,
            "sources": sources,
            "conversation_id": conv_id,
            "document_name": doc["filename"]
        })

    except Exception as e:
        return jsonify({"success": False, "error": f"Error generating answer: {str(e)}"}), 500


@app.route("/conversations", methods=["GET"])
def get_conversations():
    session_id = get_current_session_id()
    convs = database.get_all_conversations(session_id)
    return jsonify({"success": True, "conversations": convs})


@app.route("/history", methods=["GET"])
def get_history():
    session_id = get_current_session_id()
    conv_id = request.args.get("conversation_id")
    if not conv_id:
        convs = database.get_all_conversations(session_id)
        if convs:
            conv_id = convs[0]["id"]
        else:
            return jsonify({"success": True, "messages": [], "conversation_id": None})

    messages = database.get_conversation_history(conv_id, session_id)
    return jsonify({
        "success": True,
        "conversation_id": conv_id,
        "messages": messages
    })


@app.route("/clear", methods=["POST"])
def clear_chat():
    session_id = get_current_session_id()
    database.clear_session_conversations(session_id)
    return jsonify({"success": True, "message": "Chat history cleared successfully."})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1")
    print(f"Starting DocuMind on port {port} (debug={debug})...")
    app.run(host="0.0.0.0", port=port, debug=debug)
