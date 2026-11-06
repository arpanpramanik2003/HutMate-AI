# 🍽️ HutMate AI — Restaurant Operations Assistant (v2.0)

> **Your Intelligent Restaurant Operations Partner**  
> An AI-powered operational copilot for restaurant owners, managers, and kitchen staff built with **React 18**, **FastAPI**, **Groq (GPT-OSS-120B)**, **FastEmbed**, **ChromaDB**, and **SQLite**.

---

## ⚡ Overview in 30 Seconds

HutMate AI consolidates restaurant operational knowledge and live database records into a single conversational interface. It eliminates guesswork and streamlines operations across three pillars:

1. **📚 Document-Grounded Knowledge (RAG):** Extracts and indexes restaurant menus, recipes, food hygiene policies, and staff SOPs from PDF, DOCX, or TXT files using FastEmbed (`BAAI/bge-small-en-v1.5`) and ChromaDB vector search.
2. **📦 Live Operational Data Tools:** Queries real-time stock levels, order statuses, and supplier directories stored in SQLite, and **directly adds or updates inventory items via chat** with intelligent category inference and context resolution.
3. **✅ Human-Approved Actions:** Drafts operational purchase requests for kitchen inventory that require explicit human approval before updating records.

```text
                     USER
                       │
                       ▼
          REACT 18 SINGLE PAGE APP
       (Chat, Live Tables, Approvals)
                       │  REST API (JSON)
                       ▼
               FASTAPI BACKEND
                       │
                       ▼
            AGENT ORCHESTRATOR LOOP
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
    RAG SEARCH    DATA TOOLS    GROQ API
    (ChromaDB)     (SQLite)   (GPT-OSS-120B)
         │             │             │
         └─────────────┼─────────────┘
                       │
                       ▼
            GROUNDED ANSWER & CITATION
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Python:** 3.11 or 3.12 (in the included `mate` virtual environment)
- **Node.js:** v18+ (tested with v22+)
- **Groq API Key:** A free API key from [Groq Console](https://console.groq.com/keys)

---

### 2. Environment Activation & Dependencies

Open PowerShell in the project root:

```powershell
# 1. Activate the Python virtual environment
.\mate\Scripts\Activate.ps1

# 2. Build the React frontend production assets
npm run build
```

---

### 3. Configure Your Environment Variables

Create your local `.env` file from `.env.example`:

```powershell
Copy-Item .env.example .env
```

Set your Groq API key in `.env`:

```env
APP_NAME=HutMate AI
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
CHROMA_DB_DIR=./data/chroma
SQLITE_DB_PATH=./data/restaurant.db
```

> 🔒 **Security Notice:** The `.env` file and `data/` directory are strictly excluded in `.gitignore`. Never commit API keys or private databases to source control.

---

### 4. Launch the Application

Start the unified FastAPI server (serves the React UI + REST API):

```powershell
python app.py
```

Or run via Uvicorn:

```powershell
python -m uvicorn server:app --port 8000 --reload
```

Open your browser at **`http://localhost:8000`**.

*(For frontend development with hot-reload, run `npm run dev` and visit `http://localhost:5173`)*.

---

## 🖥️ How to Use the Interface

### 💬 Tab 1: Operations Chat
- Ask natural language questions about recipes, hygiene policies, ingredients, and stock.
- The agent automatically determines whether to search uploaded knowledge documents, query live database tables, modify stock levels, or draft a purchase order.
- **Conversational Inventory Management:** You can instruct the assistant to add or update items in chat! For example:
  - *User:* "Do you have cheese?" $\rightarrow$ *AI:* "No cheese found in current inventory."
  - *User:* "Then add this in the inventory for 5 packets and add sufficient category also" $\rightarrow$ *AI resolves "this" as Cheese, auto-categorizes as "Dairy", and invokes `add_inventory_item`!*
- Source citations (document title and page number) are automatically displayed when knowledge base documents are referenced.
- Expand the **"🛠️ Operational Tools Invoked"** dropdown beneath any message to inspect tool parameters and outputs in real time.

### 📊 Tab 2: Live Restaurant Data Management
You can view, modify, add, and delete operational data in real time:
- **📦 Inventory Items:** Edit quantities, units, and categories inline directly in the interactive spreadsheet, or use the **➕ Quick Add** form. Click **💾 Save Inventory Changes** to write changes to SQLite.
- **🚚 Suppliers:** Update contacts, phones, emails, and supplied categories inline, or add new suppliers. Click **💾 Save Supplier Changes** to persist.
- **📋 Orders:** Change order statuses (`PROCESSING`, `IN_TRANSIT`, `DELIVERED`, `CANCELLED`) or record new purchase orders with the **➕ Create New Order Record** form. Click **💾 Save Orders Changes** to persist.
- **Live Assistant Awareness:** Any modifications saved here are immediately visible to HutMate AI in the chat!

### ✅ Tab 3: Action Approvals (Human-in-the-Loop)
Guards operational writes and financial commitments:
- **⏳ Pending Approvals Queue:** When the AI (or staff) drafts a purchase request, an action card appears here displaying the item, quantity, supplier, and timestamp.
- **One-Click Actions:** Click **`✅ Approve`** or **`❌ Reject`**.
- **Automated Execution:** When approved:
  1. The purchase request status changes to `APPROVED` with a resolution timestamp.
  2. The item's stock in **Inventory** is automatically incremented.
  3. A new formal order (e.g. `ORD-APR0001`) with status `PROCESSING` is automatically generated in the **Orders** table!
- **📜 Approval History & Audit Trail:** Inspect all historical requests, status, and resolution timestamps.
- **➕ Manual Drafting:** Draft purchase orders manually using the built-in draft form.

### 📄 Sidebar: Uploading & Indexing Documents
1. Drag and drop any restaurant `.pdf`, `.docx`, or `.txt` file (e.g. food safety SOPs, recipes, supplier pricing).
2. Click **📥 Index Uploaded Documents**.
3. FastEmbed converts text chunks into 384-dimensional dense vectors and indexes them in ChromaDB.
4. Immediately test questions against your new documents in the chat!

---

## 🌐 Multilingual & Magic In-Chat Language Adaptation

HutMate AI features a fully autonomous language engine:
1. **Dynamic Language Detection**: Write in **English**, **Bengali (বাংলা)**, or **Hindi (हिंदी)** — the agent automatically detects your language and responds fluently without requiring manual switching.
2. **In-Chat Language Switching**: Change languages right inside the conversation:
   - *"Speak in Bengali"* or *"বাংলায় কথা বলুন"* $\rightarrow$ switches context and replies in Bengali.
   - *"Now switch to English"* or *"Talk in English"* $\rightarrow$ switches context and replies in English.
   - *"Hindi me baat karo"* or *"हिंदी में उत्तर दें"* $\rightarrow$ switches context and replies in Hindi.
3. **Banglish & Hinglish Tolerance**: Prompts like `"amader kache ki alu ache?"` or `"5 packet alu add koro"` are natively understood, mapped to canonical database fields, and replied to in Bengali.
4. **Smart Typo Tolerance (Levenshtein Distance)**: Typos such as `"potto"`, `"cheez"`, `"chikn"`, or `"tamatar"` automatically resolve to canonical inventory items.

---

## 🧩 Project Architecture & Directory Structure

```text
HutMate AI/
├── app.py                         # ASGI / FastAPI entrypoint runner
├── main.py                        # Alternative ASGI entrypoint (uvicorn main:app)
├── server.py                      # FastAPI REST API & static React server
├── requirements.txt               # Python dependency manifest
├── package.json                   # NPM workspaces definition
├── .env                           # Local environment variables (Private)
├── .env.example                   # Template for environment configuration
├── .gitignore                     # Exclusion list for secrets, venv, and databases
├── README.md                      # User guide & documentation
│
├── frontend/                      # React 18 + Vite frontend
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx                # Main container & state coordination
│   │   ├── index.css              # Application styling
│   │   ├── constants/
│   │   │   └── config.js          # Shared translations, units, and constants
│   │   └── components/
│   │       ├── common/            # Header, Sidebar, Toast components
│   │       ├── chat/              # ChatTab, ChatMessage, PromptChips
│   │       ├── data/              # DataTab, Inventory, Suppliers, Orders
│   │       └── approvals/         # ApprovalsTab, PendingQueue, AuditHistory
│   └── dist/                      # Compiled production assets
│
├── core/
│   ├── config.py                  # Typed environment settings and directory setup
│   ├── groq_client.py             # Groq SDK client connection wrapper
│   └── i18n.py                    # Multilingual detection, transliteration, typo lexicon
│
├── database/
│   ├── db.py                      # SQLite schema setup and connection manager
│   └── sample_data.py             # Demo seed script for inventory, orders, suppliers
│
├── rag/
│   ├── document_loader.py         # Text parser for PDF (pypdf), DOCX (python-docx), TXT
│   ├── chunker.py                 # Sliding-window chunker with metadata tracking
│   ├── embeddings.py              # FastEmbed model wrapper (BAAI/bge-small-en-v1.5)
│   └── retriever.py               # ChromaDB local collection search and indexing
│
├── agent/
│   ├── tools.py                   # SQLite operational functions (lookup, stock, orders, approvals)
│   └── orchestrator.py            # Bounded Groq tool-calling agent with smart category inference
│
├── data/                          # Local storage directory (auto-created, git-ignored)
│   ├── restaurant.db              # SQLite relational database
│   └── chroma/                    # Persistent ChromaDB vector database
│
├── knowledge_base/                # Built-in sample restaurant documents
│   ├── menus/
│   ├── policies/
│   └── suppliers/
│
└── tests/
    ├── test_api.py                # Automated tests for FastAPI REST routes
    ├── test_i18n.py               # Automated tests for multilingual detection, Banglish/Hinglish
    ├── test_rag.py                # Automated tests for document parsing, chunking, vector search
    └── test_tools.py              # Automated tests for inventory, orders, approval lifecycles
```

---

## 🔬 Running the Automated Test Suite

Run the full automated test suite using `pytest`:

```powershell
python -m pytest tests/ -v
```

**Test Coverage (20/20 Passing):**
- `tests/test_api.py`: Validates `/api/bootstrap`, `/api/system/reseed`, inventory CRUD, supplier CRUD, order CRUD, approval lifecycles, RAG loading, and chat endpoint mocking.
- `tests/test_i18n.py`: Validates native Bengali/Devanagari script detection, in-chat language switching, phonetic Banglish/Hinglish matching, and typo correction.
- `tests/test_rag.py`: Validates text extraction, chunking, FastEmbed embeddings, and ChromaDB semantic search.
- `tests/test_tools.py`: Validates operational tool execution and approval transitions in SQLite.

---

## 📄 License
This project is licensed under the [MIT License](LICENSE).
