import re
from typing import Dict, Any, List, Optional
from core.i18n import normalize_item_name, FOOD_ITEMS_LEXICON
from agent import tools

def run_fallback_agent(user_message: str, language: str = "en") -> Dict[str, Any]:
    """
    Deterministic rule-based operational fallback when Groq LLM API is unavailable,
    offline, or missing an API key. Executes real tools and returns structured answers.
    """
    raw = user_message.strip()
    lower = raw.lower()
    tools_used = []

    # 1. Check Recipe Feasibility (e.g. "how many biryani", "feasibility", "koto plate banano jabe")
    if any(k in lower for k in ["how many", "feasibility", "portions", "plates can we make", "koto", "banano jabe", "kitna banega"]):
        # Match dish name
        dish_name = "Dum Chicken Biryani"
        if "paneer" in lower or "butter masala" in lower:
            dish_name = "Paneer Butter Masala"
        elif "naan" in lower or "bread" in lower or "garlic" in lower:
            dish_name = "Garlic Butter Naan"

        feas = tools.check_dish_feasibility(dish_name)
        tools_used.append({"tool": "check_dish_feasibility", "args": {"dish_name": dish_name}, "result": feas})

        if feas.get("status") == "success":
            max_p = feas.get("max_portions_possible", feas.get("max_portions", 0))
            limiting = feas.get("limiting_ingredient", "None")
            if language == "bn":
                msg = f"📊 বর্তমান স্টক দিয়ে আপনি **{max_p} প্লেট {dish_name}** তৈরি করতে পারবেন। সীমাবদ্ধ উপাদান (Bottleneck): **{limiting}**।"
            elif language == "hi":
                msg = f"📊 वर्तमान स्टॉक के साथ आप **{max_p} भाग {dish_name}** तैयार कर सकते हैं। सीमित घटक (Bottleneck): **{limiting}**।"
            else:
                msg = f"📊 With current stock, you can prepare up to **{max_p} portion(s) of '{dish_name}'**. Bottleneck ingredient: **{limiting}**."
        else:
            msg = feas.get("message", "Unable to calculate feasibility.")

        return {
            "answer": msg,
            "tools_used": tools_used,
            "sources": [],
            "fallback": True,
            "detected_language": language
        }

    # 2. Record Dish Sales / Production (e.g. "sold 4 biryani", "serve kora hoyeche", "cooked 5 plates")
    sales_match = re.search(r"\b(?:sold|cooked|prepared|serve|served|becha)\s+(\d+(?:\.\d+)?)\s*(?:plates?|portions?|ta|ti)?\s*(?:of\s+)?([a-z\s]+)", lower)
    if not sales_match:
        sales_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:plates?|portions?|ta|ti)\s+([a-z\s]+)\s*(?:sold|serve|cooked)", lower)

    if sales_match:
        qty = float(sales_match.group(1))
        dish_raw = sales_match.group(2).strip()
        dish_name = "Dum Chicken Biryani"
        if "paneer" in dish_raw:
            dish_name = "Paneer Butter Masala"
        elif "naan" in dish_raw:
            dish_name = "Garlic Butter Naan"

        res = tools.record_dish_sales(dish_name, qty)
        tools_used.append({"tool": "record_dish_sales", "args": {"dish_name": dish_name, "portions": qty}, "result": res})

        if res.get("status") == "success":
            if language == "bn":
                msg = f"✅ **{qty} প্লেট {dish_name}**-এর প্রয়োজনীয় উপাদান ইনভেন্টরি থেকে সফলভাবে বাদ দেওয়া হয়েছে।"
            elif language == "hi":
                msg = f"✅ **{qty} भाग {dish_name}** के आवश्यक घटक इन्वेंट्री से सफलतापूर्वक काट लिए गए हैं।"
            else:
                msg = f"✅ Successfully deducted ingredients for **{qty} portion(s) of '{dish_name}'** from live stock."
        else:
            msg = f"⚠️ {res.get('message', 'Stock deduction failed.')}"

        return {
            "answer": msg,
            "tools_used": tools_used,
            "sources": [],
            "fallback": True,
            "detected_language": language
        }

    # 3. Low Stock / Shortages / Par Level Check
    if any(k in lower for k in ["low stock", "shortage", "shortages", "running low", "par level", "alerts", "kom ache"]):
        alerts = tools.get_low_stock_alerts()
        tools_used.append({"tool": "get_low_stock_alerts", "args": {}, "result": alerts})

        if alerts:
            lines = [f"- **{a['item_name']}**: {a['quantity']} {a['unit']} (Par: {a['min_par_level']} {a['unit']}, Shortfall: {a['shortfall']} {a['unit']}, Est. Restock: ₹{a['estimated_restock_cost']:,.2f})" for a in alerts]
            if language == "bn":
                msg = f"⚠️ **পার লেভেলের নিচে থাকা উপাদান ({len(alerts)} টি):**\n" + "\n".join(lines)
            elif language == "hi":
                msg = f"⚠️ **पार स्तर से नीचे की वस्तुएं ({len(alerts)}):**\n" + "\n".join(lines)
            else:
                msg = f"⚠️ **Critical Low Stock Alerts ({len(alerts)} items below minimum par):**\n" + "\n".join(lines)
        else:
            msg = "✅ All inventory items are currently above their minimum par levels." if language == "en" else "✅ সমস্ত ইনভেন্টরি আইটেম পার লেভেলের উপরে রয়েছে।"

        return {
            "answer": msg,
            "tools_used": tools_used,
            "sources": [],
            "fallback": True,
            "detected_language": language
        }

    # 4. Order Status Lookup (e.g. "status of ORD-1001", "ORD-1002")
    order_match = re.search(r"\b(ORD-\d{4})\b", raw.upper())
    if order_match:
        ord_num = order_match.group(1)
        ord_info = tools.get_order_status(ord_num)
        tools_used.append({"tool": "get_order_status", "args": {"order_number": ord_num}, "result": ord_info})

        if ord_info:
            msg = f"📦 **Order {ord_info['order_number']}**: {ord_info['quantity']} {ord_info['unit']} of {ord_info['item_name']} from **{ord_info['supplier_name']}**. Current Status: `{ord_info['status']}`."
        else:
            msg = f"❌ Order `{ord_num}` not found in active order registry."

        return {
            "answer": msg,
            "tools_used": tools_used,
            "sources": [],
            "fallback": True,
            "detected_language": language
        }

    # 5. Suppliers Lookup
    if any(k in lower for k in ["supplier", "suppliers", "vendor", "vendors", "contact person"]):
        sups = tools.get_supplier_details()
        tools_used.append({"tool": "get_supplier_details", "args": {}, "result": sups})
        lines = [f"- **{s['name']}** ({s.get('contact_person', 'N/A')}): {s.get('phone', '')} | Supplies: {s.get('supplied_categories', '')}" for s in sups[:5]]
        msg = "📋 **Registered Restaurant Suppliers:**\n" + "\n".join(lines)
        return {
            "answer": msg,
            "tools_used": tools_used,
            "sources": [],
            "fallback": True,
            "detected_language": language
        }

    # 6. Master Recipes & BOM Lookup
    if any(k in lower for k in ["recipe", "recipes", "bom", "cookbook", "ingredients needed"]):
        recs = tools.get_recipes()
        tools_used.append({"tool": "get_recipes", "args": {}, "result": recs})
        lines = [f"- **{r['dish_name']}** ({r['category']}): {len(r['ingredients'])} ingredients ({', '.join(i['ingredient_name'] for i in r['ingredients'][:3])}...)" for r in recs]
        msg = "📖 **Master Menu Recipes (Bill of Materials):**\n" + "\n".join(lines)
        return {
            "answer": msg,
            "tools_used": tools_used,
            "sources": [],
            "fallback": True,
            "detected_language": language
        }

    # 7. Inventory Stock Lookup (Default for food item queries)
    # Check if a food item is mentioned
    detected_item = None
    for token in re.findall(r"\w+", lower):
        if token in FOOD_ITEMS_LEXICON:
            detected_item = token
            break

    inv_items = tools.get_inventory(detected_item)
    tools_used.append({"tool": "get_inventory", "args": {"item_name": detected_item}, "result": inv_items})

    if inv_items:
        lines = [f"- **{i['item_name']}**: **{i['quantity']} {i['unit']}** (Par: {i['min_par_level']} {i['unit']}, Cost: ₹{i['cost_per_unit']}/unit, Exp: {i.get('expiry_date') or 'N/A'})" for i in inv_items[:6]]
        if language == "bn":
            msg = "📦 **বর্তমান ইনভেন্টরি স্টক:**\n" + "\n".join(lines)
        elif language == "hi":
            msg = "📦 **वर्तमान इन्वेंट्री स्टॉक:**\n" + "\n".join(lines)
        else:
            msg = "📦 **Current Inventory Stock Levels:**\n" + "\n".join(lines)
    else:
        msg = f"No inventory items found matching '{raw}'."

    return {
        "answer": msg,
        "tools_used": tools_used,
        "sources": [],
        "fallback": True,
        "detected_language": language
    }

