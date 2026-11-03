import streamlit as st
import pandas as pd
from core import config
from core.i18n import (
    LANGUAGES,
    t,
    normalize_item_name,
    get_item_localized_display,
    get_category_localized,
    get_unit_localized,
    detect_message_language,
)
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

# Initialize session language
if "lang" not in st.session_state:
    st.session_state.lang = "en"

# Sidebar: Language Selector & Operations
with st.sidebar:
    st.header("🌐 " + ("Language / ভাষা" if st.session_state.lang == "bn" else "Language / भाषा / भाषा"))
    current_idx = list(LANGUAGES.keys()).index(st.session_state.lang) if st.session_state.lang in LANGUAGES else 0
    selected_lang = st.selectbox(
        "System Language",
        options=list(LANGUAGES.keys()),
        format_func=lambda x: {"en": "🇬🇧 English", "bn": "🇧🇩 বাংলা (Bengali)", "hi": "🇮🇳 हिंदी (Hindi)"}.get(x, x),
        index=current_idx,
        key="lang_toggle_widget",
        label_visibility="collapsed"
    )
    if selected_lang != st.session_state.lang:
        st.session_state.lang = selected_lang
        # Reset default greeting in new language if untouched
        if "messages" in st.session_state and len(st.session_state.messages) == 1:
            st.session_state.messages[0]["content"] = t("welcome_message", selected_lang)
        st.rerun()

    lang = st.session_state.lang
    st.markdown("---")
    st.header(t("sidebar_sys_ops", lang))
    
    # Reset/seed demo database button
    if st.button(t("btn_reseed", lang), width="stretch"):
        seed_sample_data()
        st.success("Sample database reseeded!" if lang == "en" else "ডেমো ডেটা সফলভাবে লোড হয়েছে!")
        st.rerun()

    # Pre-load sample knowledge documents button
    if st.button(t("btn_load_samples", lang), width="stretch"):
        with st.spinner("Indexing sample documents..." if lang == "en" else "স্যাম্পল নির্দেশিকা ইন্ডেক্স করা হচ্ছে..."):
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
            st.success(f"Indexed {total_loaded} chunk(s)!" if lang == "en" else f"{total_loaded} টি অংশ ইন্ডেক্স করা হয়েছে!")
            st.rerun()

    st.markdown("---")
    st.subheader(t("sidebar_doc_upload", lang))
    st.caption(t("sidebar_doc_caption", lang))
    uploaded_files = st.file_uploader(
        "Upload files",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )
    if uploaded_files:
        if st.button(t("btn_index_docs", lang), width="stretch"):
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
    st.metric(t("metric_chunks", lang), indexed_count)

# Header
st.title(t("app_title", lang))
st.caption(t("app_caption", lang))

# Main Application Tabs
tab_chat, tab_data, tab_approvals = st.tabs([
    t("tab_chat", lang),
    t("tab_data", lang),
    t("tab_approvals", lang)
])

# ----------------- Tab 1: Operations Chat -----------------
with tab_chat:
    header_col1, header_col2 = st.columns([8, 2], vertical_alignment="center")
    with header_col1:
        st.markdown(f"### {t('chat_heading', lang)}")
        st.caption(t("chat_caption", lang))
    with header_col2:
        if st.button(t("btn_clear_chat", lang), key="clear_chat_history", width="stretch"):
            st.session_state.messages = [
                {"role": "assistant", "content": t("welcome_message", lang)}
            ]
            st.rerun()

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": t("welcome_message", lang)}
        ]

    # Dedicated scrollable container for chat history
    chat_container = st.container(height=520)

    # Chat input positioned at the end of the chat interface
    prompt = st.chat_input(
        t("chat_placeholder", lang),
        key="chat_input_query"
    )

    # Render all messages inside the chat container
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("tools_used"):
                    with st.expander("🛠️ " + ("Operational Tools Invoked" if lang == "en" else "ব্যবহৃত অপারেশনাল টুলস")):
                        st.json(msg["tools_used"])
                if msg.get("sources"):
                    st.caption(f"📚 Sources: {', '.join(set(msg['sources']))}")

        # When a prompt is submitted, render new message and response directly inside chat_container
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Dynamic Language Detection directly from the user's message
            lang_info = detect_message_language(prompt, default_lang=st.session_state.lang)
            detected_lang = lang_info["language"]
            is_explicit_switch = lang_info["is_explicit_switch"]
            detected_script = lang_info.get("detected_script")

            # If user explicitly requested language change or typed in native script, adapt session language
            if is_explicit_switch or (detected_script in ("bengali", "devanagari") and detected_lang != st.session_state.lang):
                st.session_state.lang = detected_lang
                st.session_state.lang_toggle_widget = detected_lang

            active_lang = st.session_state.lang
            spinner_text = (
                "HutMate AI is thinking and consulting operational tools..."
                if active_lang == "en" else
                ("হাটমেট এআই তথ্য বিশ্লেষণ করছে..." if active_lang == "bn" else "हटमेट एआई जानकारी का विश्लेषण कर रहा है...")
            )

            with st.chat_message("assistant"):
                with st.spinner(spinner_text):
                    try:
                        res = orchestrator.run_agent(
                            user_message=prompt,
                            conversation_history=st.session_state.messages[:-1],
                            language=active_lang
                        )
                        answer = res["answer"]
                        sources = res.get("sources", [])
                        tools_used = res.get("tools_used", [])
                        resp_lang = res.get("detected_language", active_lang)

                        # Sync language if explicit switch was acknowledged
                        if res.get("is_explicit_switch") and resp_lang in LANGUAGES:
                            st.session_state.lang = resp_lang
                            st.session_state.lang_toggle_widget = resp_lang

                        st.markdown(answer)
                        if tools_used:
                            with st.expander("🛠️ " + ("Operational Tools Invoked" if st.session_state.lang == "en" else "ব্যবহৃত অপারেশনাল টুলস")):
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
    st.markdown(f"### {t('tab_data', lang)}")
    st.caption(
        "Inspect, edit values in-place, add new items, or delete records directly in the SQLite operational database."
        if lang == "en" else
        "লাইভ ডেটাবেসে পণ্যের পরিমাণ পরিবর্তন করুন, নতুন খাদ্য উপাদান যোগ করুন বা মুছে ফেলুন।"
    )

    subtab_inv, subtab_sup, subtab_ord = st.tabs([
        t("subtab_inventory", lang),
        t("subtab_suppliers", lang),
        t("subtab_orders", lang)
    ])

    # --- Sub-tab 1: Inventory ---
    with subtab_inv:
        st.subheader("Inventory Stock Levels" if lang == "en" else "বর্তমান খাদ্যদ্রব্যের স্টক")
        inv_data = tools.get_inventory()
        inv_df = pd.DataFrame(inv_data) if inv_data else pd.DataFrame(columns=["item_name", "quantity", "unit", "category"])

        if not inv_df.empty:
            # Add dynamic localized meaning column (e.g. Potatoes -> আলু (Alu))
            meaning_label = "Local Meaning (বাংলা অর্থ)" if lang == "bn" else ("स्थानीय अर्थ (Hindi)" if lang == "hi" else "Local Meaning")
            inv_df[meaning_label] = inv_df["item_name"].apply(
                lambda name: normalize_item_name(name).get(f"display_{lang}", normalize_item_name(name)["display_bn"])
            )
            display_cols = ["item_name", meaning_label, "quantity", "unit", "category"]
            display_inv = inv_df[display_cols].copy()
        else:
            display_inv = inv_df

        edited_inv = st.data_editor(
            display_inv,
            key="inv_editor",
            num_rows="dynamic",
            width="stretch",
            column_config={
                "item_name": st.column_config.TextColumn("Item Name / খাদ্যদ্রব্য", required=True),
                meaning_label if not inv_df.empty else "Local Meaning": st.column_config.TextColumn(
                    meaning_label if not inv_df.empty else "Local Meaning", disabled=True
                ),
                "quantity": st.column_config.NumberColumn("Quantity / পরিমাণ", min_value=0.0, step=0.5, format="%.2f", required=True),
                "unit": st.column_config.SelectboxColumn("Unit / একক", options=["kg", "liters", "units", "grams", "cans", "boxes", "packets"], required=True),
                "category": st.column_config.SelectboxColumn("Category / বিভাগ", options=["Poultry", "Meat", "Produce", "Dairy", "Grains", "Spices", "Pantry", "Beverages"], required=True),
            }
        )

        col_save_inv, _ = st.columns([2, 8])
        with col_save_inv:
            if st.button(t("btn_save_inv", lang), key="save_inv_btn", width="stretch"):
                if not edited_inv.empty and "item_name" in edited_inv.columns:
                    clean_sync_df = edited_inv[["item_name", "quantity", "unit", "category"]].copy()
                    tools.sync_inventory_from_dataframe(clean_sync_df)
                    st.success("✅ Inventory updated successfully in SQLite database!" if lang == "en" else "✅ ইনভেন্টরি সফলভাবে আপডেট করা হয়েছে!")
                    st.rerun()

        with st.expander("➕ " + ("Quick Add New Inventory Item" if lang == "en" else "নতুন পণ্য যোগ করুন (Quick Add)")):
            with st.form("add_inv_form"):
                f_name = st.text_input(
                    "Item Name (supports typos/Bengali like 'potto', 'alu', 'cheese')",
                    placeholder="e.g. Potato / আলু / potto"
                )
                f_qty = st.number_input("Quantity", min_value=0.0, value=10.0, step=1.0)
                f_unit = st.selectbox("Unit", ["kg", "liters", "units", "grams", "cans", "boxes", "packets"])
                f_cat = st.selectbox("Category", ["Produce", "Dairy", "Poultry", "Meat", "Grains", "Spices", "Pantry", "Beverages"])
                submit_inv = st.form_submit_button("Add Item to Inventory" if lang == "en" else "পণ্য ইনভেন্টরিতে যোগ করুন")
                if submit_inv and f_name:
                    res = tools.upsert_inventory_item(f_name, f_qty, f_unit, f_cat)
                    st.success(f"Added: {res['item_name']} ({res.get('display_bn', '')})!")
                    st.rerun()

    # --- Sub-tab 2: Suppliers ---
    with subtab_sup:
        st.subheader("Supplier Directory" if lang == "en" else "সরবরাহকারী তালিকা")
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
            if st.button(t("btn_save_sup", lang), key="save_sup_btn", width="stretch"):
                if not edited_sup.empty and "name" in edited_sup.columns:
                    tools.sync_suppliers_from_dataframe(edited_sup)
                    st.success("✅ Supplier directory updated successfully in SQLite!" if lang == "en" else "✅ সরবরাহকারী তথ্য সফলভাবে আপডেট হয়েছে!")
                    st.rerun()

        with st.expander("➕ " + ("Quick Add New Supplier" if lang == "en" else "নতুন সরবরাহকারী যোগ করুন")):
            with st.form("add_sup_form"):
                s_name = st.text_input("Supplier Company Name", placeholder="e.g. Royal Spice Traders")
                s_contact = st.text_input("Contact Person", placeholder="e.g. Deepak Kumar")
                s_phone = st.text_input("Phone", placeholder="+91 99999 00000")
                s_email = st.text_input("Email", placeholder="contact@royalspice.com")
                s_cats = st.text_input("Categories Supplied", placeholder="Spices, Seasoning, Herbs")
                submit_sup = st.form_submit_button("Add Supplier" if lang == "en" else "সরবরাহকারী যোগ করুন")
                if submit_sup and s_name:
                    tools.upsert_supplier(s_name, s_contact, s_phone, s_email, s_cats)
                    st.success(f"Added {s_name} to suppliers!")
                    st.rerun()

    # --- Sub-tab 3: Orders ---
    with subtab_ord:
        st.subheader("Purchase Orders" if lang == "en" else "ক্রয় ও সরবরাহ অর্ডারসমূহ")
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
                "unit": st.column_config.SelectboxColumn("Unit", options=["kg", "liters", "units", "grams", "cans", "boxes", "packets"], required=True),
                "supplier_name": st.column_config.TextColumn("Supplier Name", required=True),
                "status": st.column_config.SelectboxColumn("Status", options=["PROCESSING", "IN_TRANSIT", "DELIVERED", "CANCELLED"], required=True),
            }
        )

        col_save_ord, _ = st.columns([2, 8])
        with col_save_ord:
            if st.button(t("btn_save_ord", lang), key="save_ord_btn", width="stretch"):
                if not edited_ord.empty and "order_number" in edited_ord.columns:
                    tools.sync_orders_from_dataframe(edited_ord)
                    st.success("✅ Order records updated successfully in SQLite!" if lang == "en" else "✅ অর্ডারের তথ্য সফলভাবে আপডেট হয়েছে!")
                    st.rerun()

        with st.expander("➕ " + ("Create New Order Record" if lang == "en" else "নতুন অর্ডার রেকর্ড তৈরি করুন")):
            with st.form("add_ord_form"):
                o_num = st.text_input("Order Number", placeholder="e.g. ORD-1004")
                o_item = st.text_input("Item Name", placeholder="e.g. Cooking Oil")
                o_qty = st.number_input("Quantity", min_value=1.0, value=20.0, step=1.0)
                o_unit = st.selectbox("Unit", ["kg", "liters", "units", "grams", "cans", "boxes", "packets"], key="ord_unit_select")
                o_sup = st.text_input("Supplier Name", placeholder="e.g. Golden Grain Traders")
                o_stat = st.selectbox("Status", ["PROCESSING", "IN_TRANSIT", "DELIVERED", "CANCELLED"])
                submit_ord = st.form_submit_button("Record Order" if lang == "en" else "অর্ডার রেকর্ড সংরক্ষণ করুন")
                if submit_ord and o_num and o_item:
                    tools.upsert_order(o_num, o_item, o_qty, o_unit, o_sup, o_stat)
                    st.success(f"Recorded order {o_num}!")
                    st.rerun()

# ----------------- Tab 3: Action Approvals -----------------
with tab_approvals:
    st.markdown(f"### {t('tab_approvals', lang)}")
    st.caption(
        "Safeguard operational writes: Review, approve, or reject draft purchase orders proposed by HutMate AI or kitchen staff."
        if lang == "en" else
        "অপারেশনাল অনুমোদন: এআই বা কর্মচারীদের প্রস্তাবিত ড্রাফট অর্ডার পর্যালোচনা করুন, অনুমোদন দিন অথবা বাতিল করুন।"
    )

    approval_subtab1, approval_subtab2 = st.tabs([
        t("subtab_pending", lang),
        t("subtab_history", lang)
    ])

    with approval_subtab1:
        pending_requests = tools.get_pending_purchase_requests()
        if not pending_requests:
            st.success("🎉 No pending purchase requests. All caught up!" if lang == "en" else "🎉 কোনো অপেক্ষমাণ ক্রয় প্রস্তাব নেই। সব আপডেট রয়েছে!")
        else:
            for req in pending_requests:
                with st.container(border=True):
                    col_info, col_actions = st.columns([7, 3], vertical_alignment="center")
                    with col_info:
                        norm_info = normalize_item_name(req["item_name"])
                        display_name = f"{req['item_name']} ({norm_info.get(f'display_{lang}', norm_info['display_bn'])})" if lang != "en" else req['item_name']
                        st.markdown(f"#### Request #{req['id']} — Order {display_name}")
                        st.markdown(f"**Quantity:** `{req['quantity']} {req['unit']}` &nbsp;|&nbsp; **Supplier:** `{req['supplier_name']}`")
                        st.caption(f"Requested on: {req.get('created_at', 'Just now')}")

                    with col_actions:
                        btn_c1, btn_c2 = st.columns(2)
                        with btn_c1:
                            if st.button(t("btn_approve", lang), key=f"app_{req['id']}", width="stretch"):
                                tools.resolve_purchase_request(req["id"], "APPROVED")
                                st.success(f"Request #{req['id']} Approved! Stock updated and order placed." if lang == "en" else f"রিকোয়েস্ট #{req['id']} অনুমোদিত! স্টক আপডেট হয়েছে।")
                                st.rerun()
                        with btn_c2:
                            if st.button(t("btn_reject", lang), key=f"rej_{req['id']}", width="stretch"):
                                tools.resolve_purchase_request(req["id"], "REJECTED")
                                st.warning(f"Request #{req['id']} Rejected." if lang == "en" else f"রিকোয়েস্ট #{req['id']} বাতিল করা হয়েছে।")
                                st.rerun()

        with st.expander("➕ " + ("Manually Draft a Purchase Request" if lang == "en" else "ম্যানুয়ালি পারচেস রিকোয়েস্ট তৈরি করুন")):
            with st.form("manual_draft_form"):
                d_item = st.text_input("Item Name", placeholder="e.g. Basmati Rice / আলু / Aloo")
                d_qty = st.number_input("Quantity", min_value=1.0, value=25.0, step=1.0)
                d_unit = st.selectbox("Unit", ["kg", "liters", "units", "grams", "cans", "boxes", "packets"], key="manual_unit")
                d_sup = st.text_input("Supplier Name", placeholder="e.g. Golden Grain Traders")
                submit_draft = st.form_submit_button("Submit Draft for Approval" if lang == "en" else "অনুমোদনের জন্য পাঠান")
                if submit_draft and d_item and d_sup:
                    tools.create_purchase_request(d_item, d_qty, d_unit, d_sup)
                    st.success(f"Created draft purchase request for {d_qty} {d_unit} {d_item}!")
                    st.rerun()

    with approval_subtab2:
        all_requests = tools.get_all_purchase_requests()
        if not all_requests:
            st.info("No purchase requests recorded yet." if lang == "en" else "এখনো পর্যন্ত কোনো ক্রয়ের রেকর্ড নেই।")
        else:
            df_history = pd.DataFrame(all_requests)
            st.dataframe(
                df_history,
                width="stretch",
                column_config={
                    "id": st.column_config.NumberColumn("Req #", format="%d"),
                    "item_name": st.column_config.TextColumn("Item / পণ্য"),
                    "quantity": st.column_config.NumberColumn("Quantity / পরিমাণ", format="%.2f"),
                    "unit": st.column_config.TextColumn("Unit / একক"),
                    "supplier_name": st.column_config.TextColumn("Supplier / সরবরাহকারী"),
                    "status": st.column_config.SelectboxColumn("Status", options=["PENDING_APPROVAL", "APPROVED", "REJECTED"]),
                    "created_at": st.column_config.DatetimeColumn("Created At"),
                    "resolved_at": st.column_config.DatetimeColumn("Resolved At"),
                }
            )
