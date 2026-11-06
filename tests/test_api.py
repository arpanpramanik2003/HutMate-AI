import pytest
from unittest.mock import patch
from database.sample_data import seed_sample_data
import server
from server import (
    InventoryItemModel,
    InventorySyncRequest,
    SupplierModel,
    SupplierSyncRequest,
    OrderModel,
    OrderSyncRequest,
    PurchaseRequestCreate,
    PurchaseRequestResolve,
    ChatRequest,
    ChatMessageItem,
)

def setup_module():
    """Seed demo data prior to running API test suite."""
    seed_sample_data()

def test_bootstrap_endpoint():
    data = server.get_bootstrap()
    assert "app_name" in data
    assert "inventory" in data
    assert "suppliers" in data
    assert "orders" in data
    assert "pending_requests" in data
    assert "all_requests" in data
    assert len(data["inventory"]) > 0

def test_system_reseed_endpoint():
    data = server.reseed_database()
    assert data["status"] == "success"
    assert "state" in data
    assert len(data["state"]["inventory"]) >= 7

def test_inventory_endpoints_lifecycle():
    # 1. Add / Upsert item
    item_model = InventoryItemModel(
        item_name="Test Paneer",
        quantity=12.0,
        unit="kg",
        category="Dairy"
    )
    res_add = server.add_or_update_inventory(item_model)
    assert res_add["result"]["status"] == "success"
    added_name = res_add["result"]["item_name"]
    assert any(i["item_name"] == added_name for i in res_add["inventory"])

    # 2. Sync inventory
    sync_req = InventorySyncRequest(
        items=[
            InventoryItemModel(item_name="Sync Potato", quantity=30.0, unit="kg", category="Produce"),
            InventoryItemModel(item_name="Sync Rice", quantity=45.0, unit="kg", category="Grains")
        ]
    )
    res_sync = server.sync_inventory(sync_req)
    assert res_sync["status"] == "success"
    assert len(res_sync["inventory"]) == 2

    # 3. Delete item
    res_del = server.remove_inventory_item("Sync Potato")
    assert res_del["result"]["deleted_count"] >= 1

    # Re-seed back to default
    seed_sample_data()

def test_suppliers_endpoints_lifecycle():
    # 1. Add supplier
    sup_model = SupplierModel(
        name="Himalayan Herbs Co",
        contact_person="Ramesh Thapa",
        phone="+91 99887 76655",
        email="info@himalayanherbs.com",
        supplied_categories="Spices, Herbs"
    )
    res_add = server.add_or_update_supplier(sup_model)
    assert res_add["status"] == "success"
    assert any(s["name"] == "Himalayan Herbs Co" for s in res_add["suppliers"])

    # 2. Sync suppliers
    sync_req = SupplierSyncRequest(
        items=[
            SupplierModel(
                name="Bakery Mart",
                contact_person="Sunita Sen",
                phone="+91 91234 56789",
                email="contact@bakerymart.com",
                supplied_categories="Dairy, Flour"
            )
        ]
    )
    res_sync = server.sync_suppliers(sync_req)
    assert res_sync["status"] == "success"
    assert len(res_sync["suppliers"]) == 1
    new_id = res_sync["suppliers"][0]["id"]

    # 3. Delete supplier
    res_del = server.remove_supplier(new_id)
    assert res_del["status"] == "success"
    assert len(res_del["suppliers"]) == 0

    # Re-seed back
    seed_sample_data()

def test_orders_endpoints_lifecycle():
    # 1. Add order
    ord_model = OrderModel(
        order_number="ORD-TEST-99",
        item_name="Tomatoes",
        quantity=15.0,
        unit="kg",
        supplier_name="Fresh Farm Produce",
        status="PROCESSING"
    )
    res_add = server.add_or_update_order(ord_model)
    assert res_add["status"] == "success"
    matching = [o for o in res_add["orders"] if o["order_number"] == "ORD-TEST-99"]
    assert len(matching) == 1
    ord_id = matching[0]["id"]

    # 2. Delete order
    res_del = server.remove_order(ord_id)
    assert res_del["status"] == "success"
    orders_after = res_del["orders"]
    assert not any(o["order_number"] == "ORD-TEST-99" for o in orders_after)

def test_approvals_endpoints_lifecycle():
    # 1. Draft purchase request
    draft_model = PurchaseRequestCreate(
        item_name="Cooking Oil",
        quantity=20.0,
        unit="liters",
        supplier_name="Golden Grain Traders"
    )
    res_create = server.draft_purchase_request(draft_model)
    assert res_create["status"] == "success"
    created = res_create["request"]
    req_id = created["id"]
    assert created["status"] == "PENDING_APPROVAL"

    # 2. Verify in list
    res_list = server.list_approvals()
    assert any(p["id"] == req_id for p in res_list["pending_requests"])

    # 3. Resolve request (Approve)
    resolve_model = PurchaseRequestResolve(decision="APPROVED")
    res_resolve = server.resolve_approval(req_id, resolve_model)
    assert res_resolve["status"] == "success"
    assert res_resolve["decision"] == "APPROVED"
    assert not any(p["id"] == req_id for p in res_resolve["state"]["pending_requests"])

def test_rag_load_samples_endpoint():
    res = server.load_sample_documents()
    assert res["status"] == "success"
    assert res["total_indexed_chunks"] >= 0

def test_chat_endpoint_mocked():
    mock_orchestrator_return = {
        "answer": "Current stock of Chicken Breast is 14.5 kg.",
        "sources": [],
        "tools_used": [{"tool": "get_inventory", "args": {"item_name": "Chicken"}, "result": []}],
        "detected_language": "en",
        "is_explicit_switch": False
    }

    with patch("agent.orchestrator.run_agent", return_value=mock_orchestrator_return):
        req = ChatRequest(
            message="How much chicken is in stock?",
            history=[],
            language="en"
        )
        res = server.chat_with_agent(req)
        assert "Chicken Breast is 14.5 kg" in res["answer"]
        assert len(res["tools_used"]) == 1
        assert res["active_language"] == "en"
        assert "state" in res
