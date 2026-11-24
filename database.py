import sqlite3
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = os.getenv("DOCUMIND_DB_PATH", "documind.db")


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize SQLite database tables for documents, conversations, and messages."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        filename TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_size INTEGER NOT NULL,
        pages_count INTEGER NOT NULL,
        chunks_count INTEGER NOT NULL,
        collection_name TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        title TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id TEXT NOT NULL,
        session_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        sources TEXT,
        created_at TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()


def add_document(
    doc_id: str,
    session_id: str,
    filename: str,
    file_path: str,
    file_size: int,
    pages_count: int,
    chunks_count: int,
    collection_name: str
):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO documents (id, session_id, filename, file_path, file_size, pages_count, chunks_count, collection_name, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        doc_id, session_id, filename, file_path, file_size,
        pages_count, chunks_count, collection_name, datetime.utcnow().isoformat()
    ))
    conn.commit()
    conn.close()


def get_documents_by_session(session_id: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM documents WHERE session_id = ? ORDER BY created_at DESC
    """, (session_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_document_by_id(doc_id: str, session_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM documents WHERE id = ? AND session_id = ?
    """, (doc_id, session_id))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def delete_document_record(doc_id: str, session_id: str) -> Optional[Dict[str, Any]]:
    doc = get_document_by_id(doc_id, session_id)
    if not doc:
        return None
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM documents WHERE id = ? AND session_id = ?", (doc_id, session_id))
    conn.commit()
    conn.close()
    return doc


def get_or_create_conversation(conversation_id: Optional[str], session_id: str, first_message: str = "") -> str:
    import uuid
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if conversation_id:
        cursor.execute("SELECT id FROM conversations WHERE id = ? AND session_id = ?", (conversation_id, session_id))
        row = cursor.fetchone()
        if row:
            conn.close()
            return row["id"]
            
    new_id = str(uuid.uuid4())
    # Generate clean short title from first question
    title = (first_message[:35] + "...") if len(first_message) > 35 else (first_message or "New Document Chat")
    cursor.execute("""
    INSERT INTO conversations (id, session_id, title, created_at)
    VALUES (?, ?, ?, ?)
    """, (new_id, session_id, title, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    return new_id


def add_message(conversation_id: str, session_id: str, role: str, content: str, sources: Optional[List[Dict[str, Any]]] = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    sources_json = json.dumps(sources) if sources else None
    cursor.execute("""
    INSERT INTO messages (conversation_id, session_id, role, content, sources, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (conversation_id, session_id, role, content, sources_json, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()


def get_conversation_history(conversation_id: str, session_id: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT role, content, sources, created_at FROM messages
    WHERE conversation_id = ? AND session_id = ?
    ORDER BY id ASC
    """, (conversation_id, session_id))
    rows = cursor.fetchall()
    conn.close()
    result = []
    for row in rows:
        item = dict(row)
        if item["sources"]:
            try:
                item["sources"] = json.loads(item["sources"])
            except Exception:
                item["sources"] = []
        result.append(item)
    return result


def get_all_conversations(session_id: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT c.id, c.title, c.created_at, COUNT(m.id) as message_count
    FROM conversations c
    LEFT JOIN messages m ON c.id = m.conversation_id
    WHERE c.session_id = ?
    GROUP BY c.id
    ORDER BY c.created_at DESC
    """, (session_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def clear_session_conversations(session_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    cursor.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()
