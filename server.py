from pathlib import Path
from typing import List, Optional, Dict, Any
import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from core import config
from core.i18n import (
    LANGUAGES,
    TRANSLATIONS,
    normalize_item_name,
    detect_message_language,
)
from rag.document_loader import extract_text_from_file
from rag.chunker import chunk_text
from rag.retriever import index_chunks, count_indexed_documents
from database.sample_data import seed_sample_data
from database.db import init_db
from agent import tools, orchestrator

# Ensure database tables exist on startup, and seed initial demo data if empty
init_db()
if not tools.get_inventory() and not tools.get_supplier_details():
    seed_sample_data()

app = FastAPI(
    title=config.APP_NAME,
    description="HutMate AI — Intelligent Restaurant Operations Assistant REST API",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------- Pydantic Schemas -----------------

class ChatMessageItem(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessageItem] = []
    language: str = "en"


class InventoryItemModel(BaseModel):
    item_name: str
    quantity: float
    unit: str
    category: Optional[str] = "Pantry"
    min_par_level: Optional[float] = 5.0
    cost_per_unit: Optional[float] = 0.0
    expiry_date: Optional[str] = ""


class InventorySyncRequest(BaseModel):
    items: List[InventoryItemModel]


class SupplierModel(BaseModel):
    name: str
    contact_person: Optional[str] = ""
    phone: Optional[str] = ""
    email: Optional[str] = ""
    supplied_categories: Optional[str] = ""


class SupplierSyncRequest(BaseModel):
    items: List[SupplierModel]


class OrderModel(BaseModel):
    order_number: str
    item_name: str
    quantity: float
    unit: str
    supplier_name: str
    status: str = "PROCESSING"


class OrderSyncRequest(BaseModel):
    items: List[OrderModel]


class PurchaseRequestCreate(BaseModel):
    item_name: str
    quantity: float
    unit: str
    supplier_name: str


class PurchaseRequestResolve(BaseModel):
    decision: str  # "APPROVED" or "REJECTED"


class DishSalesRequest(BaseModel):
    dish_name: str
    portions: float


# ----------------- Helper Enrichers -----------------

def _enrich_inventory(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    enriched = []
    for row in items:
        norm = normalize_item_name(row["item_name"])
        enriched.append({
            **row,
            "display_bn": norm.get("display_bn", row["item_name"]),
            "display_hi": norm.get("display_hi", row["item_name"]),
            "display_en": norm.get("display_bn", row["item_name"]),
        })
    return enriched


def _enrich_pending_requests(requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    enriched = []
    for req in requests:
        norm = normalize_item_name(req["item_name"])
        cost = req.get("estimated_cost", 0.0) or 0.0
        cost_formatted = f"₹{cost:,.2f}" if cost > 0 else "Quote pending"
        enriched.append({
            **req,
            "display_bn": norm.get("display_bn", req["item_name"]),
            "display_hi": norm.get("display_hi", req["item_name"]),
            "estimated_cost_formatted": cost_formatted,
        })
    return enriched


def _get_full_state() -> Dict[str, Any]:
    return {
        "app_name": config.APP_NAME,
        "languages": LANGUAGES,
        "translations": TRANSLATIONS,
        "indexed_chunks": count_indexed_documents(),
        "inventory": _enrich_inventory(tools.get_inventory()),
        "low_stock_alerts": tools.get_low_stock_alerts(),
        "recipes": tools.get_recipes(),
        "kitchen_sales": tools.get_kitchen_sales_log(),
        "suppliers": tools.get_supplier_details(),
        "orders": tools.get_orders(),
        "pending_requests": _enrich_pending_requests(tools.get_pending_purchase_requests()),
        "all_requests": tools.get_all_purchase_requests(),
    }


# ----------------- Bootstrap & System Endpoints -----------------

@app.get("/api/bootstrap")
def get_bootstrap():
    """Return initial application state, translations, low-stock alerts, recipes, and live tables."""
    return _get_full_state()


@app.post("/api/system/reseed")
def reseed_database():
    """Reset and seed demonstration SQLite data."""
    seed_sample_data()
    return {
        "status": "success",
        "state": _get_full_state(),
    }


@app.post("/api/rag/load-samples")
def load_sample_documents():
    """Index built-in sample documents from knowledge_base/."""
    kb_dir = Path("knowledge_base")
    total_loaded = 0
    if kb_dir.exists():
        for sample_file in kb_dir.rglob("*.txt"):
            if sample_file.is_file() and sample_file.stat().st_size > 0:
                file_bytes = sample_file.read_bytes()
                pages = extract_text_from_file(file_bytes, sample_file.name)
                chunks = chunk_text(pages)
                index_chunks(chunks)
                total_loaded += len(chunks)
    return {
        "status": "success",
        "chunks_indexed": total_loaded,
        "total_indexed_chunks": count_indexed_documents(),
    }


@app.post("/api/rag/upload")
async def upload_and_index_documents(files: List[UploadFile] = File(...)):
    """Extract text, chunk, and index uploaded PDF, DOCX, and TXT files into ChromaDB."""
    total_chunks = 0
    processed_files = []
    for uploaded in files:
        filename = uploaded.filename or "document.txt"
        ext = filename.lower().split(".")[-1]
        if ext not in ("pdf", "docx", "txt"):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format: .{ext}. Allowed: PDF, DOCX, TXT.",
            )
        file_bytes = await uploaded.read()
        pages = extract_text_from_file(file_bytes, filename)
        chunks = chunk_text(pages)
        index_chunks(chunks)
        total_chunks += len(chunks)
        processed_files.append(filename)

    return {
        "status": "success",
        "files": processed_files,
        "chunks_indexed": total_chunks,
        "total_indexed_chunks": count_indexed_documents(),
    }


# ----------------- Chat Endpoint -----------------

@app.post("/api/chat")
def chat_with_agent(payload: ChatRequest):
    """Run HutMate AI orchestrator with automatic multilingual detection and tool execution."""
    prompt = payload.message.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    current_lang = payload.language if payload.language in LANGUAGES else "en"

    # Dynamic Language Detection directly from the user's message
    lang_info = detect_message_language(prompt, default_lang=current_lang)
    detected_lang = lang_info["language"]
    is_explicit_switch = lang_info["is_explicit_switch"]
    detected_script = lang_info.get("detected_script")

    active_lang = current_lang
    if is_explicit_switch or (
        detected_script in ("bengali", "devanagari") and detected_lang != current_lang
    ):
        active_lang = detected_lang

    history_dicts = [{"role": m.role, "content": m.content} for m in payload.history]

    try:
        res = orchestrator.run_agent(
            user_message=prompt,
            conversation_history=history_dicts,
            language=active_lang,
        )
        answer = res["answer"]
        sources = list(dict.fromkeys(res.get("sources", [])))
        tools_used = res.get("tools_used", [])
        resp_lang = res.get("detected_language", active_lang)

        if res.get("is_explicit_switch") and resp_lang in LANGUAGES:
            active_lang = resp_lang

        return {
            "answer": answer,
            "sources": sources,
            "tools_used": tools_used,
            "active_language": active_lang,
            "state": _get_full_state(),
        }
    except Exception as e:
        return {
            "answer": f"⚠️ Error: {str(e)}",
            "sources": [],
            "tools_used": [],
            "active_language": active_lang,
            "error": True,
            "state": _get_full_state(),
        }


# ----------------- Inventory Endpoints -----------------

@app.get("/api/inventory")
def list_inventory():
    return _enrich_inventory(tools.get_inventory())


@app.get("/api/inventory/low-stock")
def list_low_stock_alerts():
    return tools.get_low_stock_alerts()


@app.post("/api/inventory")
def add_or_update_inventory(item: InventoryItemModel):
    if not item.item_name.strip():
        raise HTTPException(status_code=400, detail="Item name is required.")
    res = tools.upsert_inventory_item(
        item_name=item.item_name,
        quantity=item.quantity,
        unit=item.unit,
        category=item.category,
        min_par_level=item.min_par_level,
        cost_per_unit=item.cost_per_unit,
        expiry_date=item.expiry_date,
    )
    return {
        "result": res,
        "inventory": _enrich_inventory(tools.get_inventory()),
        "low_stock_alerts": tools.get_low_stock_alerts(),
    }


@app.put("/api/inventory/sync")
def sync_inventory(payload: InventorySyncRequest):
    rows = [
        {
            "item_name": i.item_name.strip(),
            "quantity": float(i.quantity),
            "unit": i.unit.strip(),
            "category": (i.category or "Pantry").strip(),
            "min_par_level": float(i.min_par_level or 5.0),
            "cost_per_unit": float(i.cost_per_unit or 0.0),
            "expiry_date": (i.expiry_date or "").strip(),
        }
        for i in payload.items
        if i.item_name.strip()
    ]
    df = pd.DataFrame(rows, columns=["item_name", "quantity", "unit", "category", "min_par_level", "cost_per_unit", "expiry_date"])
    tools.sync_inventory_from_dataframe(df)
    return {
        "status": "success",
        "inventory": _enrich_inventory(tools.get_inventory()),
        "low_stock_alerts": tools.get_low_stock_alerts(),
    }


@app.delete("/api/inventory/{identifier}")
def remove_inventory_item(identifier: str):
    res = tools.delete_inventory_item(identifier)
    return {
        "result": res,
        "inventory": _enrich_inventory(tools.get_inventory()),
        "low_stock_alerts": tools.get_low_stock_alerts(),
    }


# ----------------- Kitchen Recipes & Sales Endpoints (BOM) -----------------

@app.get("/api/recipes")
def list_recipes(dish_name: Optional[str] = None):
    """Retrieve recipes with Bill of Materials ingredient breakdown."""
    return tools.get_recipes(dish_name)


@app.get("/api/recipes/{dish_name}/feasibility")
def check_recipe_feasibility(dish_name: str):
    """Calculate portions possible based on current stock levels."""
    return tools.check_dish_feasibility(dish_name)


@app.post("/api/kitchen/sales")
def record_kitchen_dish_sales(payload: DishSalesRequest):
    """Deduct ingredient quantities from inventory for cooked/sold dishes."""
    if not payload.dish_name.strip():
        raise HTTPException(status_code=400, detail="Dish name is required.")
    if payload.portions <= 0:
        raise HTTPException(status_code=400, detail="Portions must be greater than zero.")

    res = tools.record_dish_sales(payload.dish_name.strip(), float(payload.portions))
    return {
        "result": res,
        "state": _get_full_state(),
    }


# ----------------- Suppliers Endpoints -----------------

@app.get("/api/suppliers")
def list_suppliers():
    return tools.get_supplier_details()


@app.post("/api/suppliers")
def add_or_update_supplier(supplier: SupplierModel):
    if not supplier.name.strip():
        raise HTTPException(status_code=400, detail="Supplier name is required.")
    tools.upsert_supplier(
        supplier.name,
        supplier.contact_person or "",
        supplier.phone or "",
        supplier.email or "",
        supplier.supplied_categories or "",
    )
    return {
        "status": "success",
        "suppliers": tools.get_supplier_details(),
    }


@app.put("/api/suppliers/sync")
def sync_suppliers(payload: SupplierSyncRequest):
    rows = [
        {
            "name": s.name.strip(),
            "contact_person": (s.contact_person or "").strip(),
            "phone": (s.phone or "").strip(),
            "email": (s.email or "").strip(),
            "supplied_categories": (s.supplied_categories or "").strip(),
        }
        for s in payload.items
        if s.name.strip()
    ]
    df = pd.DataFrame(
        rows,
        columns=["name", "contact_person", "phone", "email", "supplied_categories"],
    )
    tools.sync_suppliers_from_dataframe(df)
    return {
        "status": "success",
        "suppliers": tools.get_supplier_details(),
    }


@app.delete("/api/suppliers/{supplier_id}")
def remove_supplier(supplier_id: int):
    tools.delete_supplier(supplier_id)
    return {
        "status": "success",
        "suppliers": tools.get_supplier_details(),
    }


# ----------------- Orders Endpoints -----------------

@app.get("/api/orders")
def list_orders():
    return tools.get_orders()


@app.post("/api/orders")
def add_or_update_order(order: OrderModel):
    if not order.order_number.strip() or not order.item_name.strip():
        raise HTTPException(status_code=400, detail="Order number and item name are required.")
    tools.upsert_order(
        order.order_number,
        order.item_name,
        order.quantity,
        order.unit,
        order.supplier_name,
        order.status,
    )
    return {
        "status": "success",
        "orders": tools.get_orders(),
    }


@app.put("/api/orders/sync")
def sync_orders(payload: OrderSyncRequest):
    rows = [
        {
            "order_number": o.order_number.strip().upper(),
            "item_name": o.item_name.strip(),
            "quantity": float(o.quantity),
            "unit": o.unit.strip(),
            "supplier_name": o.supplier_name.strip(),
            "status": o.status.strip().upper(),
        }
        for o in payload.items
        if o.order_number.strip() and o.item_name.strip()
    ]
    df = pd.DataFrame(
        rows,
        columns=["order_number", "item_name", "quantity", "unit", "supplier_name", "status"],
    )
    tools.sync_orders_from_dataframe(df)
    return {
        "status": "success",
        "orders": tools.get_orders(),
    }


@app.delete("/api/orders/{order_id}")
def remove_order(order_id: int):
    tools.delete_order(order_id)
    return {
        "status": "success",
        "orders": tools.get_orders(),
    }


# ----------------- Action Approvals Endpoints -----------------

@app.get("/api/approvals")
def list_approvals():
    return {
        "pending_requests": _enrich_pending_requests(tools.get_pending_purchase_requests()),
        "all_requests": tools.get_all_purchase_requests(),
    }


@app.post("/api/approvals")
def draft_purchase_request(payload: PurchaseRequestCreate):
    if not payload.item_name.strip() or not payload.supplier_name.strip():
        raise HTTPException(status_code=400, detail="Item name and supplier name are required.")
    created = tools.create_purchase_request(
        payload.item_name,
        payload.quantity,
        payload.unit,
        payload.supplier_name,
    )
    return {
        "status": "success",
        "request": created,
        "pending_requests": _enrich_pending_requests(tools.get_pending_purchase_requests()),
        "all_requests": tools.get_all_purchase_requests(),
    }


@app.post("/api/approvals/{request_id}/resolve")
def resolve_approval(request_id: int, payload: PurchaseRequestResolve):
    decision = payload.decision.upper().strip()
    if decision not in ("APPROVED", "REJECTED"):
        raise HTTPException(status_code=400, detail="Decision must be APPROVED or REJECTED.")
    updated = tools.resolve_purchase_request(request_id, decision)
    if not updated:
        raise HTTPException(status_code=404, detail="Pending request not found or already resolved.")
    return {
        "status": "success",
        "decision": decision,
        "state": _get_full_state(),
    }


# ----------------- Static React Frontend Serving -----------------

FRONTEND_DIST = Path(__file__).parent / "frontend" / "dist"

if FRONTEND_DIST.exists() and (FRONTEND_DIST / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        candidate = FRONTEND_DIST / full_path
        if full_path and candidate.exists() and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")
