# DocuMind – AI-Powered PDF Document Assistant 🧠📄

> **DocuMind** is a production-grade, full-stack Retrieval-Augmented Generation (RAG) web application that empowers users to upload PDF books, research papers, and technical manuals to ask questions and receive instant, context-grounded AI answers with page citations.

Built with **Flask**, **LangChain**, **ChromaDB**, **Groq LLM (`openai/gpt-oss-120b`)**, **HuggingFace Embeddings**, and a **ChatGPT-inspired dark UI** featuring the interactive **Morphing AI Thinking Orb** inspired by 21st.dev (`@anark17r`).

---

## 🌟 Key Features

- **Dynamic PDF Ingestion & Chunking**: Drag-and-drop or browse any PDF up to 32MB. Documents are parsed using `PyPDFLoader` and split with `RecursiveCharacterTextSplitter` (1,000 characters with 200 character overlap).
- **Dense Vector Search with MMR Retrieval**: Employs HuggingFace Embeddings and ChromaDB Maximum Marginal Relevance (MMR) retrieval (`k=4`, `fetch_k=10`, `lambda_mult=0.5`) to eliminate redundancy and extract the most relevant context chunks.
- **Strictly Grounded LLM Generation**: Powered by Groq's high-speed `openai/gpt-oss-120b` inference engine. Governed by a system prompt that answers strictly from document context and explicitly admits when information is absent.
- **Transparent Source Citations**: Every generated response includes clickable source badges referencing the exact PDF page numbers and text excerpts.
- **ChatGPT-Inspired User Experience**:
  - Polished dark mode layout (`#0A0B0E`, `#111318`).
  - Left sidebar with New Chat, multi-document management, and conversation history.
  - Welcome screen with ambient glow and suggested question prompts.
  - Multiline composer with auto-resizing, PDF attachment button, and shortcut navigation (Enter to send, Shift+Enter for newlines).
  - Mobile slide-out drawer navigation.
- **21st.dev Morphing AI Thinking Orb**: Features an organic, state-aware glowing gradient orb that pulses during idle states and ripples during document reasoning.
- **Multi-Tenant User & Session Isolation**: Session-based collection separation and SQLite persistence prevent cross-user data leakage.
- **Cloud Deployment Ready**: Fully configured for **Render** using **Gunicorn**, **Render Persistent Disks**, and `render.yaml`.

---

## 🏗️ System Architecture & RAG Pipeline

```mermaid
flowchart TD
    subgraph Client["Frontend Interface (Vanilla HTML5 / CSS3 / ES6 JS)"]
        UI["ChatGPT-Style Dark Interface"]
        Orb["21st.dev Morphing AI Thinking Orb"]
        Composer["Composer & PDF Attachment"]
    end

    subgraph Server["Flask REST Backend (main.py)"]
        API["Flask Routes (/upload, /chat, /history)"]
        SessionMgr["Session & SQLite Storage (documind.db)"]
    end

    subgraph Pipeline["RAG Pipeline (create_db.py)"]
        Loader["PyPDFLoader (Dynamic Upload)"]
        Splitter["RecursiveCharacterTextSplitter (1000 / 200)"]
        Embedder["HuggingFaceEmbeddings (all-mpnet-base-v2)"]
        VectorDB["ChromaDB Vector Store (MMR Retriever)"]
        LLM["ChatGroq (openai/gpt-oss-120b)"]
    end

    UI -->|1. Upload PDF| API
    API -->|2. Ingest & Parse| Loader
    Loader --> Splitter
    Splitter --> Embedder
    Embedder -->|3. Index Chunks| VectorDB
    
    Composer -->|4. User Query| API
    API -->|5. MMR Query (k=4, fetch_k=10)| VectorDB
    VectorDB -->|6. Context + Page Citations| API
    API -->|7. Strict Context Prompt| LLM
    LLM -->|8. Grounded Answer| API
    API -->|9. Render Markdown + Badges| UI
    API -->|Persist History| SessionMgr
```

---

## 📂 Project Structure

```
RAG project/
│
├── .venv/                         # Python virtual environment
├── templates/
│   └── index.html                 # Semantic ChatGPT-style frontend template
│
├── static/
│   ├── css/
│   │   └── style.css              # Dark theme, glassmorphism & MorphOrb animations
│   │
│   ├── js/
│   │   └── script.js              # Vanilla JS frontend state & async fetch controller
│   │
│   └── images/                    # UI icons and static assets
│
├── uploads/                       # User-uploaded PDFs (session-isolated)
├── chroma_db/                     # Persistent ChromaDB vector storage
│
├── document loaders/              # Sample test documents & reference scripts
│   ├── deeplearning.pdf
│   ├── GRU.pdf
│   └── notes.txt
│
├── retrievers/                    # RAG retrieval experiments
│   ├── arixv_retreiver.py
│   ├── mmr.py
│   └── multiquery.py
│
├── vector store/
│   └── DB.py
│
├── database.py                    # SQLite database persistence layer (chats, docs)
├── create_db.py                   # Modular RAG ingestion, chunking & MMR retriever
├── main.py                        # Production Flask web application & API
├── test_app.py                    # End-to-end automated integration test suite
├── requirements.txt               # Production Python dependencies
├── Procfile                       # Gunicorn start script for web deployment
├── render.yaml                    # Infrastructure-as-code for Render deployment
├── .env                           # Local environment secrets (ignored by Git)
├── .gitignore                     # Git ignore rules
└── README.md                      # Complete project documentation
```

---

## 🛠️ Technology Stack

| Layer | Technology | Details |
| :--- | :--- | :--- |
| **Backend Framework** | Flask 3.1+ | Python WSGI web framework, session management |
| **Production Server** | Gunicorn 27+ | Multi-worker WSGI HTTP server |
| **Orchestration** | LangChain / LangChain Core | RAG pipeline, prompt templates, chains |
| **Embeddings** | HuggingFace Embeddings | `sentence-transformers/all-mpnet-base-v2` |
| **Vector Database** | ChromaDB 0.5+ | Vector storage, persistent collections, MMR search |
| **LLM Inference** | Groq API (`langchain-groq`) | `openai/gpt-oss-120b` |
| **PDF Extraction** | PyPDF / PyPDFLoader | Page-by-page text parsing with metadata |
| **Text Chunking** | RecursiveCharacterTextSplitter | 1,000 chunk size, 200 overlap |
| **Chat Database** | SQLite 3 | Conversation history, document metadata |
| **Frontend** | HTML5, CSS3, Vanilla JS | No heavy JS frameworks required |
| **Markdown & Security** | Marked.js + DOMPurify | Safe client-side markdown rendering with XSS defense |
| **Design Language** | 21st.dev + ChatGPT | Morphing AI thinking orb, dark modern aesthetic |

---

## 🚀 Local Setup & Installation

### 1. Prerequisites
- **Python 3.10, 3.11, or 3.12** installed on your machine.
- A **Groq Cloud API Key** (obtain free from [console.groq.com](https://console.groq.com/keys)).
- Git installed.

### 2. Clone Repository
```bash
git clone https://github.com/your-username/documind.git
cd documind
```

### 3. Create and Activate Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Create a `.env` file in the project root:
```ini
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
SECRET_KEY=your_random_flask_secret_key_here
CHROMA_DB_PATH=chroma_db
DOCUMIND_DB_PATH=documind.db
FLASK_DEBUG=True
PORT=5000
```

> **Security Note:** Never commit your `.env` file to Git. It is already added to `.gitignore`.

### 6. Run Integration Tests
Verify that all components (upload, embedding, MMR retrieval, and Groq generation) are working:
```bash
python test_app.py
```

### 7. Start the Local Server
```bash
python main.py
```
Open your browser and navigate to:
```
http://localhost:5000
```

---

## 🌐 Public Deployment Guide (Render)

DocuMind is designed for seamless deployment to **Render** using a persistent disk for ChromaDB vector storage.

### Step 1: Push Code to GitHub
1. Initialize Git (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Initial commit of DocuMind application"
   ```
2. Create a new repository on [GitHub](https://github.com/new) named `documind`.
3. Link and push your repository:
   ```bash
   git remote add origin https://github.com/your-username/documind.git
   git branch -M main
   git push -u origin main
   ```

### Step 2: Deploy to Render via Blueprint (`render.yaml`)
1. Log in to your [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** and select **Blueprint**.
3. Connect your `documind` GitHub repository.
4. Render will automatically detect `render.yaml`.
5. Under Environment Variables:
   - Provide your `GROQ_API_KEY`.
6. Click **Apply**.

### Step 3: Manual Deployment (Alternative to Blueprint)
If creating a Web Service manually:
- **Environment**: `Python`
- **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
- **Start Command**: `gunicorn main:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
- **Plan**: Starter (Recommended, to support embedding generation in RAM)
- **Environment Variables**:
  - `PYTHON_VERSION`: `3.11.9`
  - `GROQ_API_KEY`: `<Your Groq API Key>`
  - `SECRET_KEY`: `<Click Generate>`
  - `CHROMA_DB_PATH`: `/var/data/chroma_db`
  - `DOCUMIND_DB_PATH`: `/var/data/documind.db`
  - `FLASK_DEBUG`: `False`
- **Disks** (Under Service Settings > Disks):
  - **Name**: `documind-data`
  - **Mount Path**: `/var/data`
  - **Size**: `10 GB`

### ⚠️ Important Note on Render Plans & Storage
- **Free Instance Spin-Down**: Render's Free tier does not attach persistent disks. On the Free tier, vector embeddings stored in the local filesystem reset when the instance restarts or spins down after inactivity.
- **Render Persistent Disks**: Persistent disks require Render's **Starter** plan ($7/month + disk storage). If you deploy on the Free tier, users can upload documents and chat during their active session, but vector stores and uploaded PDFs will not persist indefinitely across restarts unless a Persistent Disk is attached.

---

## 🧪 Testing the Web Interface

1. **Upload a PDF**: Drag and drop any document (e.g. `document loaders/GRU.pdf`) into the central dropzone or click the paperclip attachment icon.
2. **Observe the Morphing Orb**: Watch the 21st.dev thinking orb pulse as the backend splits pages into 1,000-character chunks and computes dense embeddings.
3. **Ask a Question**:
   - Type *"What are the key mechanisms of a GRU?"*
   - Or click one of the suggested cards: *"Summarize this document"*.
4. **Inspect Source Citations**: Notice the `📄 Page X` citation badges attached below each AI answer.
5. **Manage Documents**: Switch between multiple uploaded documents in the sidebar or click the trash icon to delete a document and its ChromaDB collection.

---

## 📜 License
This project is open-source and available under the [MIT License](LICENSE).
