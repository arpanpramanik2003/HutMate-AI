# 🍽️ HutMate AI — Restaurant Operations Assistant

> **Your Intelligent Restaurant Operations Partner**  
> An AI-powered operational copilot for restaurant owners, managers, and kitchen staff built with **Streamlit**, **Groq (GPT-OSS-120B)**, **FastEmbed**, **ChromaDB**, and **SQLite**.

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
              STREAMLIT INTERFACE
       (Chat, Live Tables, Approvals)
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
- **Python:** 3.11 or 3.12 (already installed in the included `mate` virtual environment)
- **Groq API Key:** A free API key from [Groq Console](https://console.groq.com/keys)

---

### 2. Environment Activation & Setup

Open your terminal or PowerShell in the project root:

```powershell
# 1. Activate the included virtual environment
.\mate\Scripts\Activate.ps1

# (Optional verification)
python -V
pip list
```

---

### 3. Configure Your Environment Variables

Create your local `.env` file from the provided `.env.example`:

```powershell
# Copy the example configuration
Copy-Item .env.example .env
```

Open `.env` in any editor and insert your Groq API key:

```env
APP_NAME=HutMate AI
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
CHROMA_DB_DIR=./data/chroma
SQLITE_DB_PATH=./data/restaurant.db
```

> 🔒 **Security Notice:** The `.env` file and `data/` directory are strictly excluded in `.gitignore`. Never commit API keys or private databases to source control.

---

### 4. Seed the Sample Database

Populate initial demonstration inventory, orders, and supplier directory records:

```powershell
python -m database.sample_data
```

*Output:*
```text
Database schema initialized successfully.
Demo data seeded successfully.
```

---

### 5. Launch the Application

Start the Streamlit application:

```powershell
streamlit run app.py
```

Streamlit will automatically open your browser at **`http://localhost:8501`**.

---

## 🖥️ How to Use the Interface

### 💬 Tab 1: Operations Chat
- Ask natural language questions about your restaurant.
- The agent automatically determines whether to search uploaded knowledge documents, query live database tables, modify stock levels, or draft a purchase order.
- **Conversational Inventory Management:** You can instruct the assistant to add or update items in chat! For example, say: *"Add 5 packets of cheese to inventory and add sufficient category"* or follow up on a lookup:
  - *User:* "Do you have cheese?" $\rightarrow$ *AI:* "No cheese found in current inventory."
  - *User:* "Then add this in the inventory for 5 packets and add sufficient category also" $\rightarrow$ *AI resolves "this" as Cheese, auto-categorizes as "Dairy", and invokes `add_inventory_item`!*
- Source citations (document title and page number) are automatically displayed when knowledge base documents are referenced.
- Expand the **"🛠️ Operational Tools Invoked"** dropdown beneath any message to inspect tool parameters and outputs in real time.

### 📊 Tab 2: Live Restaurant Data Management
You can view, modify, add, and delete operational data in real time:
- **📦 Inventory Items:** Edit quantities, units, and categories inline directly in the interactive spreadsheet (`st.data_editor`), or use the **➕ Quick Add** form. Click **💾 Save Inventory Changes** to write changes to SQLite.
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
- **📜 Approval History & Audit Trail:** Switch to this sub-tab to inspect all historical requests, who created them, their status, and when they were resolved.
- **➕ Manual Drafting:** You can also draft purchase orders manually using the built-in draft form.

### 📄 Sidebar: Uploading & Indexing Documents
1. Drag and drop any restaurant `.pdf`, `.docx`, or `.txt` file (e.g. food safety SOPs, recipes, supplier pricing).
2. Click **📥 Index Uploaded Documents**.
3. FastEmbed converts text chunks into 384-dimensional dense vectors and indexes them in ChromaDB.
4. Immediately test questions against your new documents in the chat!

---

## 🌐 Multilingual & Magic In-Chat Language Adaptation

HutMate AI features a fully autonomous language engine:
1. **Dynamic Language Detection**: Write in **English**, **Bengali (বাংলা)**, or **Hindi (हिंदी)** — the agent automatically detects your language and responds fluently in that language without requiring you to touch the sidebar.
2. **In-Chat Language Switching**: Change languages right inside the conversation! Tell the bot:
   - *"Speak in Bengali"* or *"বাংলায় কথা বলুন"* $\rightarrow$ switches context and replies in Bengali.
   - *"Now switch to English"* or *"Talk in English"* $\rightarrow$ switches context and replies in English.
   - *"Hindi me baat karo"* or *"हिंदी में उत्तर दें"* $\rightarrow$ switches context and replies in Hindi.
3. **Banglish & Hinglish Tolerance**: Prompts like `"amader kache ki alu ache?"` or `"5 packet alu add koro"` are natively understood, mapped to canonical database fields, and replied to in Bengali.
4. **Smart Typo Tolerance (Levenshtein Distance)**: Typos such as `"potto"`, `"cheez"`, `"chikn"`, or `"tamatar"` automatically resolve to canonical inventory items.

---

## 🧪 Demo Scenarios to Try

| Question / Action | What the System Does | Expected Outcome |
| :--- | :--- | :--- |
| *"What is our food storage policy?"* | Searches ChromaDB via `search_knowledge_base` | Returns food hygiene guidelines with document & page citation. |
| *"আমাদের কাছে কি আলু আছে?"* | Detects Bengali, normalizes to `Potatoes`, checks stock | Responds fluently in Bengali with current stock levels. |
| *"৫ প্যাকেট চিজ যোগ করুন"* | Detects Bengali, infers category `Dairy`, invokes `add_inventory_item` | Confirms addition in Bengali; stock increments in SQLite. |
| *"Do you have cheese?"* | Calls `get_inventory(item_name='cheese')` | Reports that no cheese is currently found in stock. |
| *"Then add this in the inventory for 5 packets and add sufficient category also"* | Resolves context ("this" = Cheese), infers category (`Dairy`), calls `add_inventory_item` | Confirms addition of 5.0 packets of Cheese under Dairy, visible immediately in Tab 2! |
| *"Now speak in Bengali from now on"* | Explicit language switch | Agent confirms and adopts Bengali for future conversation. |
| *"What is the status of order ORD-1001?"* | Calls `get_order_status(order_number='ORD-1001')` | Returns status (`DELIVERED`), quantity (`100.0 kg Basmati Rice`), and supplier. |
| *"Prepare a purchase request for 25 kg of Basmati Rice from Golden Grain Traders."* | Calls `create_purchase_request(...)` | Confirms draft creation and surfaces request in the **Action Approvals** tab. |

---

## 🧩 Project Architecture & Directory Structure

```text
HutMate AI/
├── app.py                  # Streamlit application UI (Chat, Data, Approvals, File Uploader)
├── requirements.txt        # Python dependency manifest
├── .env                    # Local environment variables (Private)
├── .env.example            # Template for environment configuration
├── .gitignore              # Exclusion list for secrets, venv, and databases
├── README.md               # User guide & documentation
│
├── core/
│   ├── config.py           # Typed environment settings and directory setup
│   └── groq_client.py      # Groq SDK client connection & completion wrapper
│
├── database/
│   ├── db.py               # SQLite schema setup and connection manager
│   └── sample_data.py      # Demo seed script for inventory, orders, and suppliers
│
├── rag/
│   ├── document_loader.py  # Text parser for PDF (pypdf), DOCX (python-docx), and TXT
│   ├── chunker.py          # Sliding-window chunker with metadata tracking
│   ├── embeddings.py       # FastEmbed model wrapper (BAAI/bge-small-en-v1.5)
│   └── retriever.py        # ChromaDB local collection search and indexing
│
├── agent/
│   ├── tools.py            # SQLite operational functions (lookup, add/update stock, orders, approvals)
│   └── orchestrator.py     # Bounded Groq tool-calling agent with smart category inference
│
├── data/                   # Local storage directory (auto-created)
│   ├── restaurant.db       # SQLite relational database
│   └── chroma/             # Persistent ChromaDB vector database
│
├── knowledge_base/         # Default folder for sample restaurant documents
│   ├── menus/
│   ├── policies/
│   └── suppliers/
│
└── tests/
    ├── test_i18n.py        # Automated tests for multilingual detection, Banglish/Hinglish, and typo correction
    ├── test_rag.py         # Automated tests for document parsing, chunking, and vector search
    └── test_tools.py       # Automated tests for inventory, orders, and approval lifecycles
```

---

## 🔬 Running the Automated Test Suite

Run the full automated test suite using `pytest`:

```powershell
python -m pytest tests/ -v
```

**Test Coverage:**
- `test_detect_language_script` & `test_detect_explicit_commands`: Validates native Bengali/Devanagari script detection and in-chat language switching.
- `test_detect_banglish_and_hinglish`: Validates phonetic Banglish & Hinglish conversational matching.
- `test_fuzzy_and_typos`: Validates Levenshtein distance error tolerance for ingredients.
- `test_document_extraction_and_chunking`: Validates text extraction and sliding window metadata preservation.
- `test_rag_indexing_and_retrieval`: Validates FastEmbed embeddings and ChromaDB semantic cosine similarity search.
- `test_inventory_lookup`: Validates live SQLite inventory matching.
- `test_order_lookup`: Validates order retrieval by order code.
- `test_supplier_lookup`: Validates fuzzy supplier directory matching.
- `test_purchase_request_lifecycle`: Validates draft creation, pending queue appearance, approval state transition, and automated inventory quantity incrementation.

---

## ⚙️ Configuration Reference

| Environment Variable | Default Value | Description |
| :--- | :--- | :--- |
| `APP_NAME` | `HutMate AI` | Display name of the application. |
| `GROQ_API_KEY` | *(Required)* | Your Groq API key from console.groq.com. |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | Target language model hosted on Groq. |
| `CHROMA_DB_DIR` | `./data/chroma` | Directory for local persistent ChromaDB storage. |
| `SQLITE_DB_PATH` | `./data/restaurant.db`| File path for the operational SQLite database. |

---

## ❓ Frequently Asked Questions & Troubleshooting

#### 1. Why do I see a warning about `GROQ_API_KEY` missing?
You need to add a valid Groq API key in your `.env` file:
```env
GROQ_API_KEY=gsk_your_key_here
```
Get a key for free from [Groq Console](https://console.groq.com/keys).

#### 2. How do I reset the demo data?
Click the **🔄 Reset / Seed Demo Data** button in the Streamlit sidebar, or run:
```powershell
python -m database.sample_data
```

#### 3. Where are the embeddings stored?
Embeddings are computed locally using **FastEmbed** and stored in `./data/chroma`. No vector data leaves your local machine.

---

## 📄 License
This project is licensed under the [MIT License](LICENSE).

