# HutMate AI — Simplified Project Plan

> **Project:** HutMate AI  
> **Title:** AI-Powered Restaurant Operations Assistant  
> **Goal:** Build a working, easy-to-demonstrate AI restaurant assistant with the fewest moving parts.

---

## 1. Recommended Approach

Build HutMate AI as a **single Python application using Streamlit**.

You do not need a separate Next.js frontend and FastAPI backend for this version. Streamlit provides the visible interface and runs the Python application behind it. You can demonstrate the chat, document upload, RAG search, live sample data, and approval workflow from one application.

This is still a real application with backend logic; it simply avoids maintaining a separate frontend and API server.

## 2. Simplified Technology Stack

| Part | Recommended technology | Why |
|---|---|---|
| User interface | **Streamlit** | Build chat, upload, tables and dashboard in Python |
| Programming language | **Python** | One language for the complete application |
| LLM | **GPT-OSS-120B via Groq API** | Understand questions and generate answers |
| LLM client | **Groq Python SDK** | Connect Python to Groq |
| Document reading | **pypdf, python-docx** | Read PDF and DOCX files |
| Embeddings | **FastEmbed** | Convert document chunks and questions into vectors |
| Vector database | **ChromaDB** | Store and search document embeddings locally |
| Operational data | **SQLite** | Store sample inventory, orders and suppliers simply |
| Data access | **Python functions + sqlite3** | No separate API or ORM required initially |
| Configuration | **python-dotenv** | Load API key and settings from `.env` |
| Testing | **pytest** | Test core functions |

### Keep the first version simple

**Use:**
- Streamlit instead of Next.js.
- Direct Python function calls instead of FastAPI endpoints.
- SQLite instead of a hosted PostgreSQL setup.
- ChromaDB instead of PostgreSQL + pgvector.
- A small Python agent/tool loop instead of a large agent framework.

**Do not add initially:**
- FastAPI.
- Next.js or React.
- Supabase.
- PostgreSQL.
- SQLAlchemy or Alembic.
- Docker or Kubernetes.
- LangChain or LangGraph unless a later requirement genuinely needs them.

You can migrate to these technologies later if the project grows.

---

## 3. Simple Architecture

```text
                 USER
                   |
                   v
            STREAMLIT APP
          (Chat + Dashboard)
                   |
                   v
          PYTHON APPLICATION
                   |
          +--------+---------+
          |        |         |
          v        v         v
        RAG      DATA      AI AGENT
      SEARCH    TOOLS
          |        |         |
          v        v         v
      CHROMA DB  SQLITE    GROQ API
      Documents  Inventory GPT-OSS-120B
                 Orders
                 Suppliers
          |        |         |
          +--------+---------+
                   |
                   v
             FINAL ANSWER
```

The Streamlit application calls Python functions directly. There is no separate REST API server in this simplified design.

---

## 4. Main Features

### Feature 1 — AI Restaurant Chat

Users can ask restaurant-related questions in a chat interface.

Examples:
- What is our food storage policy?
- Which ingredients are used in Chicken Biryani?
- How should staff handle customer complaints?
- How much chicken is currently available?

The application sends the question to the Python agent, which chooses the appropriate information source.

### Feature 2 — Document-Based RAG

Allow the user to upload:
- Restaurant menus.
- Food safety policies.
- Staff SOPs.
- Supplier documents.

Processing workflow:

```text
Upload PDF / DOCX
       |
       v
Extract text
       |
       v
Split into chunks
       |
       v
Generate embeddings
       |
       v
Store in ChromaDB
       |
       v
Retrieve relevant chunks
       |
       v
Send context to Groq
       |
       v
Answer with source
```

### Feature 3 — Live Restaurant Data

Use SQLite to store demonstration data for:

- Inventory.
- Orders.
- Suppliers.
- Menu items.

Create simple Python functions such as:

```python
get_inventory(item_name)
get_order_status(order_id)
get_supplier_details(supplier_name)
```

These functions query SQLite and return the current records. The AI must use these functions for live-data questions instead of guessing.

### Feature 4 — Simple AI Agent

The agent decides whether the user needs:

1. Document search.
2. Inventory lookup.
3. Order lookup.
4. Supplier lookup.
5. A purchase-request draft.

Start with a small, sequential tool-calling loop. Validate every tool name and argument in Python. Do not give the model unrestricted SQL access.

### Feature 5 — Purchase Request Approval

Example:

User: "Prepare a purchase request for 20 kg of chicken."

The application:
1. Checks current inventory.
2. Retrieves supplier details if needed.
3. Creates a draft purchase request.
4. Displays it in Streamlit.
5. Waits for the user to click **Approve** or **Reject**.
6. Records the result in SQLite.

For the demo, use sample data. Do not connect to a real purchasing system or send actual supplier orders.

---

## 5. Suggested Simple Folder Structure

Keep your existing project root, but simplify the implementation folders. You do not need to preserve unused FastAPI and Next.js directories for this version.

```text
mothers-hut/
│
├── app.py                  # Streamlit entry point
├── requirements.txt        # Project dependencies
├── .env                    # Private API key (never commit)
├── .env.example            # Placeholder configuration
├── .gitignore
│
├── core/
│   ├── config.py           # Application settings
│   └── groq_client.py      # Groq connection
│
├── rag/
│   ├── document_loader.py  # PDF / DOCX extraction
│   ├── chunker.py          # Text chunking
│   ├── embeddings.py       # Embedding generation
│   └── retriever.py        # ChromaDB search
│
├── agent/
│   ├── orchestrator.py     # Agent decision and tool loop
│   └── tools.py            # Inventory, order, supplier tools
│
├── database/
│   ├── db.py               # SQLite connection and setup
│   └── sample_data.py      # Demo data
│
├── knowledge_base/
│   ├── menus/
│   ├── policies/
│   └── suppliers/
│
├── data/
│   └── restaurant.db       # Local SQLite database
│
└── tests/
    ├── test_rag.py
    └── test_tools.py
```

This is a proposed simplified structure. Reuse existing files where useful; do not delete your current folders until you have checked whether they contain work you need.

---

## 6. Development Workflow — Build in This Order

### Step 1 — Environment

- Activate the existing `mate` virtual environment.
- Create or update the root `requirements.txt`.
- Install the dependencies.
- Create `.env` and `.env.example`.
- Add `.env`, database files and generated vector data to `.gitignore`.

### Step 2 — Streamlit Interface

- Create `app.py`.
- Add the HutMate AI title and basic layout.
- Add a chat interface using Streamlit chat components.
- Add a document uploader.
- Confirm the app starts with:

```bash
streamlit run app.py
```

### Step 3 — Groq Connection

- Create `core/groq_client.py`.
- Load the API key from `.env`.
- Connect to GPT-OSS-120B through Groq.
- Test a simple prompt before adding agent logic.

### Step 4 — SQLite Sample Database

- Create the SQLite database.
- Add sample inventory, orders, suppliers and menu records.
- Write and test the Python lookup functions.

### Step 5 — Document Ingestion

- Accept PDF and DOCX uploads.
- Extract and clean text.
- Split text into chunks.
- Generate embeddings.
- Save vectors and metadata in ChromaDB.

### Step 6 — RAG Question Answering

- Convert the user's question into an embedding.
- Retrieve relevant chunks from ChromaDB.
- Send the question and retrieved context to Groq.
- Display an answer and its document source.

### Step 7 — Agent and Tools

- Register the allowed Python tools.
- Let the model request a tool when needed.
- Validate tool names and arguments.
- Execute the Python function.
- Return its result to the model.
- Display the final answer.

### Step 8 — Approval Workflow

- Create purchase-request drafts.
- Display the request in Streamlit.
- Add Approve and Reject controls.
- Store the status and action history in SQLite.

### Step 9 — Final Demo and Testing

Test these example scenarios:

| Demo question/action | Expected behavior |
|---|---|
| "What is our food storage policy?" | RAG answer with source |
| "What ingredients are used in Chicken Biryani?" | Menu document retrieval |
| "How much chicken is available?" | SQLite inventory lookup |
| "What is the status of order ORD-1001?" | SQLite order lookup |
| "Show supplier details for ABC Foods." | SQLite supplier lookup |
| "Prepare a request for 20 kg chicken." | Draft request and approval UI |

---

## 7. Security and Important Rules

- Revoke any API key previously exposed and create a new one.
- Keep the replacement Groq key only in the local `.env` file.
- Never expose the Groq key in Streamlit page content or source control.
- Add `.env` to `.gitignore`.
- Validate uploaded files and enforce a file-size limit.
- Do not allow the model to execute arbitrary SQL.
- Use fixed Python functions for database access.
- Require explicit approval before recording a write action.
- Treat uploaded documents as untrusted content.
- For a multi-restaurant version, add user authentication and enforce restaurant-level access on every query. The initial local demo can use one sample restaurant.

---

## 8. Simplified Project Completion Checklist

- [ ] Streamlit app launches.
- [ ] Groq model responds.
- [ ] PDF and DOCX uploads work.
- [ ] Documents are chunked and indexed.
- [ ] RAG retrieves relevant passages.
- [ ] Answers show source information.
- [ ] SQLite inventory lookup works.
- [ ] Order lookup works.
- [ ] Supplier lookup works.
- [ ] Agent chooses the correct tool.
- [ ] Purchase request can be drafted.
- [ ] Approve/Reject controls work.
- [ ] Important actions are stored.
- [ ] Demo scenarios pass.

---

## 9. Final Recommendation

For the first working version, use this stack:

**Python + Streamlit + Groq GPT-OSS-120B + FastEmbed + ChromaDB + SQLite.**

This is enough to demonstrate the important AI concepts:
- RAG.
- Embeddings and vector search.
- LLM integration.
- Agent tool calling.
- Live database retrieval.
- Human-in-the-loop approval.

You do not need a separate frontend/backend architecture to demonstrate these features. Streamlit provides the interface, while your Python modules implement the application logic.

**Build one small feature at a time. Run it, test it, and only then move to the next step.**
