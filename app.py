import streamlit as st
import pandas as pd
from core import config
from rag.document_loader import extract_text_from_file
from rag.chunker import chunk_text
from rag.retriever import index_chunks, count_indexed_documents
from database.sample_data import seed_sample_data
from database.db import init_db
from agent import tools, orchestrator

# Page setup
st.set_page_config(
    page_title=config.APP_NAME,
    page_icon="🍽️",
    layout="wide",
)

# Ensure database tables exist on startup
init_db()

st.title("🍽️ HutMate AI")
st.caption("Intelligent Restaurant Operations Assistant — Streamlit Edition")

# Sidebar
with st.sidebar:
    st.header("⚙️ System Operations")
    
    # Reset/seed demo database button
    if st.button("🔄 Reset / Seed Demo SQLite Data", width="stretch"):
        seed_sample_data()
        st.success("Sample database reseeded!")
        st.rerun()

    # Pre-load sample knowledge documents button
    if st.button("📚 Index Built-in Sample Documents", width="stretch"):
        with st.spinner("Indexing sample menus & policy documents..."):
            from pathlib import Path
            kb_dir = Path("knowledge_base")
            total_loaded = 0
            for sample_file in kb_dir.rglob("*.txt"):
                if sample_file.is_file() and sample_file.stat().st_size > 0:
                    with open(sample_file, "rb") as f:
                        file_bytes = f.read()
                    pages = extract_text_from_file(file_bytes, sample_file.name)
                    chunks = chunk_text(pages)
                    index_chunks(chunks)
                    total_loaded += len(chunks)
            st.success(f"Indexed {total_loaded} chunk(s) from knowledge_base/!")
            st.rerun()

    st.markdown("---")
    st.subheader("📄 Upload Restaurant Documents (RAG)")
    st.caption(
        "Upload your restaurant's **Food Safety SOPs**, **Recipes & Menus**, or **Supplier Agreements** (PDF, DOCX, TXT). "
        "The AI will search these to answer staff questions and cite exact page sources."
    )
    uploaded_files = st.file_uploader(
        "Upload files to knowledge base",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
    )
    if uploaded_files:
        if st.button("📥 Index Uploaded Documents", width="stretch"):
            total_chunks = 0
            with st.spinner("Processing & generating FastEmbed vectors..."):
                for uploaded in uploaded_files:
                    file_bytes = uploaded.read()
                    pages = extract_text_from_file(file_bytes, uploaded.name)
                    chunks = chunk_text(pages)
                    index_chunks(chunks)
                    total_chunks += len(chunks)
            st.success(f"Successfully indexed {total_chunks} chunk(s) into ChromaDB!")
            st.rerun()

    indexed_count = count_indexed_documents()
    st.metric("Total Indexed Knowledge Chunks", indexed_count)

# Main Application Tabs
tab_chat, tab_data, tab_approvals = st.tabs(["💬 Operations Chat", "📊 Live Restaurant Data", "✅ Action Approvals"])

# ----------------- Tab 1: Operations Chat -----------------
with tab_chat:
    header_col1, header_col2 = st.columns([8, 2], vertical_alignment="center")
    with header_col1:
        st.markdown("### Conversational Assistant")
        st.caption("Ask questions about recipes, policies, current stock, orders, or ask to draft a purchase order.")
    with header_col2:
        if st.button("🗑️ Clear Chat", key="clear_chat_history", width="stretch"):
            st.session_state.messages = [
                {"role": "assistant", "content": "Hello! I am HutMate AI. How can I help with your restaurant operations today?"}
            ]
            st.rerun()

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I am HutMate AI. How can I help with your restaurant operations today?"}
        ]

    # Dedicated scrollable container for chat history
    chat_container = st.container(height=520)

    # Chat input positioned at the end of the chat interface
    prompt = st.chat_input(
        "Ask HutMate AI (e.g., 'What is our chicken storage policy?' or 'How much chicken is in stock?')",
        key="chat_input_query"
    )

    # Render all messages inside the chat container
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("tools_used"):
                    with st.expander("🛠️ Operational Tools Invoked"):
                        st.json(msg["tools_used"])
                if msg.get("sources"):
                    st.caption(f"📚 Sources: {', '.join(set(msg['sources']))}")

        # When a prompt is submitted, render new message and response directly inside chat_container
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("HutMate AI is thinking and consulting operational tools..."):
                    try:
                        res = orchestrator.run_agent(
                            user_message=prompt,
                            conversation_history=st.session_state.messages[:-1]
                        )
                        answer = res["answer"]
                        sources = res.get("sources", [])
                        tools_used = res.get("tools_used", [])

                        st.markdown(answer)
                        if tools_used:
                            with st.expander("🛠️ Operational Tools Invoked"):
                                st.json(tools_used)
                        if sources:
                            st.caption(f"📚 Sources: {', '.join(set(sources))}")

                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": answer,
                            "sources": sources,
                            "tools_used": tools_used,
                        })
                    except Exception as e:
                        err_msg = f"⚠️ Error: {str(e)}"
                        st.error(err_msg)
                        st.session_state.messages.append({"role": "assistant", "content": err_msg})
            st.rerun()

# ----------------- Tab 2: Live Operational Data -----------------
with tab_data:
    st.markdown("### 📊 Live Operational Data Management")
    st.caption("Inspect, edit values in-place, add new items, or delete records directly in the SQLite operational database.")

    subtab_inv, subtab_sup, subtab_ord = st.tabs(["📦 Inventory Items", "🚚 Suppliers", "📋 Orders"])

    # --- Sub-tab 1: Inventory ---
    with subtab_inv:
        st.subheader("Inventory Stock Levels")
        inv_data = tools.get_inventory()
        inv_df = pd.DataFrame(inv_data) if inv_data else pd.DataFrame(columns=["item_name", "quantity", "unit", "category"])
        display_inv = inv_df[["item_name", "quantity", "unit", "category"]].copy() if not inv_df.empty else inv_df

        edited_inv = st.data_editor(
            display_inv,
            key="inv_editor",
            num_rows="dynamic",
            width="stretch",
            column_config={
                "item_name": st.column_config.TextColumn("Item Name", required=True),
                "quantity": st.column_config.NumberColumn("Quantity", min_value=0.0, step=0.5, format="%.2f", required=True),
                "unit": st.column_config.SelectboxColumn("Unit", options=["kg", "liters", "units", "grams", "cans", "boxes"], required=True),
                "category": st.column_config.SelectboxColumn("Category", options=["Poultry", "Meat", "Produce", "Dairy", "Grains", "Spices", "Pantry", "Beverages"], required=True),
            }
        )

        col_save_inv, _ = st.columns([2, 8])
        with col_save_inv:
            if st.button("💾 Save Inventory Changes", key="save_inv_btn", width="stretch"):
                if not edited_inv.empty and "item_name" in edited_inv.columns:
                    tools.sync_inventory_from_dataframe(edited_inv)
                    st.success("✅ Inventory updated successfully in SQLite database!")
                    st.rerun()

        with st.expander("➕ Quick Add New Inventory Item"):
            with st.form("add_inv_form"):
                f_name = st.text_input("Item Name", placeholder="e.g. Olive Oil")
                f_qty = st.number_input("Quantity", min_value=0.0, value=10.0, step=1.0)
                f_unit = st.selectbox("Unit", ["kg", "liters", "units", "grams", "cans", "boxes"])
                f_cat = st.selectbox("Category", ["Poultry", "Meat", "Produce", "Dairy", "Grains", "Spices", "Pantry", "Beverages"])
                submit_inv = st.form_submit_button("Add Item to Inventory")
                if submit_inv and f_name:
                    tools.upsert_inventory_item(f_name, f_qty, f_unit, f_cat)
                    st.success(f"Added {f_name} to inventory!")
                    st.rerun()

    # --- Sub-tab 2: Suppliers ---
    with subtab_sup:
        st.subheader("Supplier Directory")
        sup_data = tools.get_supplier_details()
        sup_df = pd.DataFrame(sup_data) if sup_data else pd.DataFrame(columns=["name", "contact_person", "phone", "email", "supplied_categories"])
        display_sup = sup_df[["name", "contact_person", "phone", "email", "supplied_categories"]].copy() if not sup_df.empty else sup_df

        edited_sup = st.data_editor(
            display_sup,
            key="sup_editor",
            num_rows="dynamic",
            width="stretch",
            column_config={
                "name": st.column_config.TextColumn("Supplier Company", required=True),
                "contact_person": st.column_config.TextColumn("Contact Person"),
                "phone": st.column_config.TextColumn("Phone"),
                "email": st.column_config.TextColumn("Email"),
                "supplied_categories": st.column_config.TextColumn("Categories Supplied"),
            }
        )

        col_save_sup, _ = st.columns([2, 8])
        with col_save_sup:
            if st.button("💾 Save Supplier Changes", key="save_sup_btn", width="stretch"):
                if not edited_sup.empty and "name" in edited_sup.columns:
                    tools.sync_suppliers_from_dataframe(edited_sup)
                    st.success("✅ Supplier directory updated successfully in SQLite!")
                    st.rerun()

        with st.expander("➕ Quick Add New Supplier"):
            with st.form("add_sup_form"):
                s_name = st.text_input("Supplier Company Name", placeholder="e.g. Royal Spice Traders")
                s_contact = st.text_input("Contact Person", placeholder="e.g. Deepak Kumar")
                s_phone = st.text_input("Phone", placeholder="+91 99999 00000")
                s_email = st.text_input("Email", placeholder="contact@royalspice.com")
                s_cats = st.text_input("Categories Supplied", placeholder="Spices, Seasoning, Herbs")
                submit_sup = st.form_submit_button("Add Supplier")
                if submit_sup and s_name:
                    tools.upsert_supplier(s_name, s_contact, s_phone, s_email, s_cats)
                    st.success(f"Added {s_name} to suppliers!")
                    st.rerun()

    # --- Sub-tab 3: Orders ---
    with subtab_ord:
        st.subheader("Purchase Orders")
        ord_data = tools.get_orders()
        ord_df = pd.DataFrame(ord_data) if ord_data else pd.DataFrame(columns=["order_number", "item_name", "quantity", "unit", "supplier_name", "status"])
        display_ord = ord_df[["order_number", "item_name", "quantity", "unit", "supplier_name", "status"]].copy() if not ord_df.empty else ord_df

        edited_ord = st.data_editor(
            display_ord,
            key="ord_editor",
            num_rows="dynamic",
            width="stretch",
            column_config={
                "order_number": st.column_config.TextColumn("Order #", required=True),
                "item_name": st.column_config.TextColumn("Item", required=True),
                "quantity": st.column_config.NumberColumn("Quantity", min_value=0.0, step=1.0, format="%.2f", required=True),
                "unit": st.column_config.SelectboxColumn("Unit", options=["kg", "liters", "units", "grams", "cans", "boxes"], required=True),
                "supplier_name": st.column_config.TextColumn("Supplier Name", required=True),
                "status": st.column_config.SelectboxColumn("Status", options=["PROCESSING", "IN_TRANSIT", "DELIVERED", "CANCELLED"], required=True),
            }
        )

        col_save_ord, _ = st.columns([2, 8])
        with col_save_ord:
            if st.button("💾 Save Orders Changes", key="save_ord_btn", width="stretch"):
                if not edited_ord.empty and "order_number" in edited_ord.columns:
                    tools.sync_orders_from_dataframe(edited_ord)
                    st.success("✅ Order records updated successfully in SQLite!")
                    st.rerun()

        with st.expander("➕ Create New Order Record"):
            with st.form("add_ord_form"):
                o_num = st.text_input("Order Number", placeholder="e.g. ORD-1004")
                o_item = st.text_input("Item Name", placeholder="e.g. Cooking Oil")
                o_qty = st.number_input("Quantity", min_value=1.0, value=20.0, step=1.0)
                o_unit = st.selectbox("Unit", ["kg", "liters", "units", "grams", "cans", "boxes"], key="ord_unit_select")
                o_sup = st.text_input("Supplier Name", placeholder="e.g. Golden Grain Traders")
                o_stat = st.selectbox("Status", ["PROCESSING", "IN_TRANSIT", "DELIVERED", "CANCELLED"])
                submit_ord = st.form_submit_button("Record Order")
                if submit_ord and o_num and o_item:
                    tools.upsert_order(o_num, o_item, o_qty, o_unit, o_sup, o_stat)
                    st.success(f"Recorded order {o_num}!")
                    st.rerun()

# ----------------- Tab 3: Action Approvals -----------------
with tab_approvals:
    st.markdown("### 📝 Human-in-the-Loop Action Approvals")
    st.caption("Safeguard operational writes: Review, approve, or reject draft purchase orders proposed by HutMate AI or kitchen staff.")

    approval_subtab1, approval_subtab2 = st.tabs(["⏳ Pending Approvals Queue", "📜 Approval History & Audit Trail"])

    with approval_subtab1:
        pending_requests = tools.get_pending_purchase_requests()
        if not pending_requests:
            st.success("🎉 No pending purchase requests. All caught up!")
        else:
            for req in pending_requests:
                with st.container(border=True):
                    col_info, col_actions = st.columns([7, 3], vertical_alignment="center")
                    with col_info:
                        st.markdown(f"#### Request #{req['id']} — Order {req['item_name']}")
                        st.markdown(f"**Quantity:** `{req['quantity']} {req['unit']}` &nbsp;|&nbsp; **Supplier:** `{req['supplier_name']}`")
                        st.caption(f"Requested on: {req.get('created_at', 'Just now')}")

                    with col_actions:
                        btn_c1, btn_c2 = st.columns(2)
                        with btn_c1:
                            if st.button("✅ Approve", key=f"app_{req['id']}", width="stretch"):
                                tools.resolve_purchase_request(req["id"], "APPROVED")
                                st.success(f"Request #{req['id']} Approved! Stock updated and order placed.")
                                st.rerun()
                        with btn_c2:
                            if st.button("❌ Reject", key=f"rej_{req['id']}", width="stretch"):
                                tools.resolve_purchase_request(req["id"], "REJECTED")
                                st.warning(f"Request #{req['id']} Rejected.")
                                st.rerun()

        with st.expander("➕ Manually Draft a Purchase Request"):
            with st.form("manual_draft_form"):
                d_item = st.text_input("Item Name", placeholder="e.g. Basmati Rice")
                d_qty = st.number_input("Quantity", min_value=1.0, value=25.0, step=1.0)
                d_unit = st.selectbox("Unit", ["kg", "liters", "units", "grams", "cans", "boxes"], key="manual_unit")
                d_sup = st.text_input("Supplier Name", placeholder="e.g. Golden Grain Traders")
                submit_draft = st.form_submit_button("Submit Draft for Approval")
                if submit_draft and d_item and d_sup:
                    tools.create_purchase_request(d_item, d_qty, d_unit, d_sup)
                    st.success(f"Created draft purchase request for {d_qty} {d_unit} {d_item}!")
                    st.rerun()

    with approval_subtab2:
        all_requests = tools.get_all_purchase_requests()
        if not all_requests:
            st.info("No purchase requests recorded yet.")
        else:
            df_history = pd.DataFrame(all_requests)
            st.dataframe(
                df_history,
                width="stretch",
                column_config={
                    "id": st.column_config.NumberColumn("Req #", format="%d"),
                    "item_name": st.column_config.TextColumn("Item"),
                    "quantity": st.column_config.NumberColumn("Quantity", format="%.2f"),
                    "unit": st.column_config.TextColumn("Unit"),
                    "supplier_name": st.column_config.TextColumn("Supplier"),
                    "status": st.column_config.SelectboxColumn("Status", options=["PENDING_APPROVAL", "APPROVED", "REJECTED"]),
                    "created_at": st.column_config.DatetimeColumn("Created At"),
                    "resolved_at": st.column_config.DatetimeColumn("Resolved At"),
                }
            )
