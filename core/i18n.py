"""Multilingual Internationalization (i18n), Food Translations, and Smart Fuzzy Typo Correction."""

import re
from typing import Dict, Any, Optional, Tuple

# Supported languages
LANGUAGES = {
    "en": "English",
    "bn": "বাংলা (Bengali)",
    "hi": "हिंदी (Hindi)"
}

# UI String Translations
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "app_title": {
        "en": "🍽️ HutMate AI",
        "bn": "🍽️ হাটমেট এআই (HutMate AI)",
        "hi": "🍽️ हटमेट एआई (HutMate AI)"
    },
    "app_caption": {
        "en": "Intelligent Restaurant Operations Assistant — Multilingual Edition",
        "bn": "স্মার্ট রেস্তোরাঁ অপারেশন সহকারী — বহুভাষিক সংস্করণ",
        "hi": "स्मार्ट रेस्तरां संचालन सहायक — बहुभाषी संस्करण"
    },
    "tab_chat": {
        "en": "💬 Operations Chat",
        "bn": "💬 অপারেশন চ্যাট",
        "hi": "💬 संचालन चैट"
    },
    "tab_data": {
        "en": "📊 Live Restaurant Data",
        "bn": "📊 লাইভ রেস্তোরাঁর তথ্য",
        "hi": "📊 लाइव रेस्तरां डेटा"
    },
    "tab_approvals": {
        "en": "✅ Action Approvals",
        "bn": "✅ অ্যাকশন অনুমোদন",
        "hi": "✅ कार्रवाई अनुमोदन"
    },
    "sidebar_sys_ops": {
        "en": "⚙️ System Operations",
        "bn": "⚙️ সিস্টেম সেটিংস ও অপারেশন",
        "hi": "⚙️ सिस्टम संचालन"
    },
    "btn_reseed": {
        "en": "🔄 Reset / Seed Demo SQLite Data",
        "bn": "🔄 ডেমো ডেটা রিসেট / পুনরায় লোড করুন",
        "hi": "🔄 डेमो डेटा रीसेट / पुनः लोड करें"
    },
    "btn_load_samples": {
        "en": "📚 Index Built-in Sample Documents",
        "bn": "📚 স্যাম্পল রেস্তোরাঁ নির্দেশিকা ইন্ডেক্স করুন",
        "hi": "📚 नमूना दस्तावेज इंडेक्स करें"
    },
    "sidebar_doc_upload": {
        "en": "📄 Upload Restaurant Documents (RAG)",
        "bn": "📄 রেস্তোরাঁর নথি আপলোড করুন (RAG)",
        "hi": "📄 रेस्तरां दस्तावेज अपलोड करें (RAG)"
    },
    "sidebar_doc_caption": {
        "en": "Upload menus, policies, or supplier guides (PDF, DOCX, TXT). HutMate AI will cite exact page numbers.",
        "bn": "মেনু, খাদ্য সুরক্ষা নির্দেশিকা বা সরবরাহকারী চুক্তি (PDF, DOCX, TXT) আপলোড করুন। এআই পৃষ্ঠার নম্বর সহ উত্তর দেবে।",
        "hi": "मेनू, नीतियां या आपूर्तिकर्ता गाइड अपलोड करें (PDF, DOCX, TXT)। एआई सटीक पृष्ठ संख्या बताएगा।"
    },
    "btn_index_docs": {
        "en": "📥 Index Uploaded Documents",
        "bn": "📥 আপলোড করা নথি ইন্ডেক্স করুন",
        "hi": "📥 अपलोड किए गए दस्तावेज इंडेक्स करें"
    },
    "metric_chunks": {
        "en": "Total Indexed Knowledge Chunks",
        "bn": "মোট ইন্ডেক্স করা নথির অংশ (Chunks)",
        "hi": "कुल इंडेक्स किए गए ज्ञान खंड"
    },
    "chat_heading": {
        "en": "Conversational Assistant",
        "bn": "কথোপকথন সহায়ক (AI Assistant)",
        "hi": "बातचीत सहायक"
    },
    "chat_caption": {
        "en": "Ask questions about recipes, policies, stock, orders, or ask to draft a purchase order.",
        "bn": "রেসিপি, নীতি, বর্তমান স্টক, অর্ডার বা কেনাকাটার রিকুইজিশন তৈরি করতে যেকোনো প্রশ্ন জিজ্ঞাসা করুন।",
        "hi": "व्यंजनों, नीतियों, स्टॉक, ऑर्डर के बारे में प्रश्न पूछें, या खरीदारी का मसौदा तैयार करने को कहें।"
    },
    "btn_clear_chat": {
        "en": "🗑️ Clear Chat",
        "bn": "🗑️ চ্যাট মুছুন",
        "hi": "🗑️ चैट साफ़ करें"
    },
    "chat_placeholder": {
        "en": "Ask HutMate AI (e.g. 'How much chicken is in stock?' or 'Do we have cheese?')",
        "bn": "হাটমেট এআই-কে জিজ্ঞাসা করুন (যেমন 'স্টকে কতটা মুরগির মাংস আছে?' বা 'আমাদের কি আলু আছে?')",
        "hi": "हटमेट एआई से पूछें (जैसे 'स्टॉक में कितना चिकन है?' या 'क्या हमारे पास आलू है?')"
    },
    "welcome_message": {
        "en": "Hello! I am HutMate AI, your restaurant operations assistant. How can I assist you today?",
        "bn": "নমস্কার! আমি হাটমেট এআই (HutMate AI), আপনার রেস্তোরাঁ অপারেশন সহকারী। আজ আপনাকে কীভাবে সাহায্য করতে পারি?",
        "hi": "नमस्ते! मैं हटमेट एआई (HutMate AI) हूं, आपका रेस्तरां संचालन सहायक। आज मैं आपकी क्या सहायता कर सकता हूँ?"
    },
    "subtab_inventory": {
        "en": "📦 Inventory Items",
        "bn": "📦 ইনভেন্টরি পণ্য (স্টক)",
        "hi": "📦 इन्वेंटरी आइटम"
    },
    "subtab_suppliers": {
        "en": "🚚 Suppliers",
        "bn": "🚚 সরবরাহকারী তালিকা (Suppliers)",
        "hi": "🚚 आपूर्तिकर्ता"
    },
    "subtab_orders": {
        "en": "📋 Orders",
        "bn": "📋 অর্ডার সমূহ",
        "hi": "📋 ऑर्डर"
    },
    "btn_save_inv": {
        "en": "💾 Save Inventory Changes",
        "bn": "💾 ইনভেন্টরির পরিবর্তন সংরক্ষণ করুন",
        "hi": "💾 इन्वेंटरी परिवर्तन सहेजें"
    },
    "btn_save_sup": {
        "en": "💾 Save Supplier Changes",
        "bn": "💾 সরবরাহকারী তথ্য সংরক্ষণ করুন",
        "hi": "💾 आपूर्तिकर्ता परिवर्तन सहेजें"
    },
    "btn_save_ord": {
        "en": "💾 Save Orders Changes",
        "bn": "💾 অর্ডারের পরিবর্তন সংরক্ষণ করুন",
        "hi": "💾 ऑर्डर परिवर्तन सहेजें"
    },
    "subtab_pending": {
        "en": "⏳ Pending Approvals Queue",
        "bn": "⏳ অনুমোদনের অপেক্ষমাণ তালিকা",
        "hi": "⏳ लंबित अनुमोदन कतार"
    },
    "subtab_history": {
        "en": "📜 Approval History & Audit Trail",
        "bn": "📜 অনুমোদনের ইতিহাস ও অডিট লগ",
        "hi": "📜 अनुमोदन इतिहास और ऑडिट लॉग"
    },
    "btn_approve": {
        "en": "✅ Approve",
        "bn": "✅ অনুমোদন করুন",
        "hi": "✅ स्वीकृत करें"
    },
    "btn_reject": {
        "en": "❌ Reject",
        "bn": "❌ বাতিল করুন",
        "hi": "❌ अस्वीकृत करें"
    }
}

def t(key: str, lang: str = "en") -> str:
    """Return the translated string for a given key and language code."""
    lang_dict = TRANSLATIONS.get(key, {})
    return lang_dict.get(lang, lang_dict.get("en", key))


# ----------------- Comprehensive Food Knowledge & Translations -----------------

FOOD_ITEMS_LEXICON = {
    "potato": {
        "canonical": "Potatoes",
        "bn": "আলু (Alu)",
        "hi": "आलू (Aloo)",
        "category": "Produce",
        "default_unit": "kg",
        "aliases": ["potato", "potatoes", "potto", "potatos", "patato", "patatos", "aaloo", "aloo", "alu", "allu", "আলু"]
    },
    "tomato": {
        "canonical": "Tomatoes",
        "bn": "টমেটো (Tomato)",
        "hi": "टमाटर (Tamatar)",
        "category": "Produce",
        "default_unit": "kg",
        "aliases": ["tomato", "tomatoes", "tometo", "tamato", "tamatar", "tamater", "tomto", "টমেটো"]
    },
    "onion": {
        "canonical": "Yellow Onions",
        "bn": "পেঁয়াজ (Peyaj)",
        "hi": "प्याज (Pyaaz)",
        "category": "Produce",
        "default_unit": "kg",
        "aliases": ["onion", "onions", "yellow onions", "pyaj", "piyaj", "pyaz", "oinon", "oniyon", "peyaj", "peaj", "পেঁয়াজ"]
    },
    "chicken": {
        "canonical": "Chicken Breast",
        "bn": "মুরগির মাংস (Murgir Mangsho)",
        "hi": "चिकन / मुर्गा (Chicken)",
        "category": "Poultry",
        "default_unit": "kg",
        "aliases": ["chicken", "chiken", "chikn", "chickin", "chicken breast", "murgi", "murga", "mangsho", "মুরগির মাংস"]
    },
    "rice": {
        "canonical": "Basmati Rice",
        "bn": "বাসমতি চাল (Basmati Chal)",
        "hi": "बासमती चावल (Basmati Rice)",
        "category": "Grains",
        "default_unit": "kg",
        "aliases": ["rice", "basmati rice", "basmati", "basmti", "chawal", "chal", "bhat", "চাল", "বাসমতি চাল"]
    },
    "cheese": {
        "canonical": "Cheese",
        "bn": "পনির / চিজ (Paneer / Cheese)",
        "hi": "पनीर / चीज़ (Paneer / Cheese)",
        "category": "Dairy",
        "default_unit": "packets",
        "aliases": ["cheese", "cheez", "chese", "paneer", "panir", "pneer", "chiz", "পনির", "চিজ"]
    },
    "oil": {
        "canonical": "Cooking Oil",
        "bn": "রান্নার তেল (Rannar Tel)",
        "hi": "खाना पकाने का तेल (Cooking Oil)",
        "category": "Pantry",
        "default_unit": "liters",
        "aliases": ["cooking oil", "oil", "tel", "refined oil", "mustard oil", "সরষের তেল", "তেল", "রান্নার তেল"]
    },
    "yogurt": {
        "canonical": "Yogurt",
        "bn": "দই (Doi / Yogurt)",
        "hi": "दही (Dahi)",
        "category": "Dairy",
        "default_unit": "kg",
        "aliases": ["yogurt", "yoghurt", "curd", "dahi", "doi", "দই"]
    },
    "garam_masala": {
        "canonical": "Garam Masala",
        "bn": "গরম মশলা (Garam Masala)",
        "hi": "गरम मसाला (Garam Masala)",
        "category": "Spices",
        "default_unit": "kg",
        "aliases": ["garam masala", "garam masala blend", "masala", "spices", "mosla", "গরম মশলা"]
    },
    "garlic": {
        "canonical": "Garlic",
        "bn": "রসুন (Rosun)",
        "hi": "लहसुन (Lahsun)",
        "category": "Produce",
        "default_unit": "kg",
        "aliases": ["garlic", "rosun", "roshun", "lahsun", "lasun", "রসুন"]
    },
    "ginger": {
        "canonical": "Ginger",
        "bn": "আদা (Ada)",
        "hi": "अदरक (Adrak)",
        "category": "Produce",
        "default_unit": "kg",
        "aliases": ["ginger", "adrak", "ada", "aada", "আদা"]
    },
    "milk": {
        "canonical": "Milk",
        "bn": "দুধ (Dudh)",
        "hi": "दूध (Doodh)",
        "category": "Dairy",
        "default_unit": "liters",
        "aliases": ["milk", "dudh", "doodh", "দুধ"]
    },
    "flour": {
        "canonical": "Wheat Flour (Atta)",
        "bn": "আটা / ময়দা (Atta / Maida)",
        "hi": "आटा / मैदा (Atta / Maida)",
        "category": "Grains",
        "default_unit": "kg",
        "aliases": ["flour", "atta", "maida", "wheat flour", "aata", "আটা", "ময়দা"]
    },
    "butter": {
        "canonical": "Butter",
        "bn": "মাখন (Makhon / Butter)",
        "hi": "मक्खन (Makkhan)",
        "category": "Dairy",
        "default_unit": "kg",
        "aliases": ["butter", "makkhan", "makhan", "makhon", "মাখন"]
    },
    "paneer": {
        "canonical": "Fresh Paneer",
        "bn": "তাজা পনির (Fresh Paneer)",
        "hi": "ताज़ा पनीर (Fresh Paneer)",
        "category": "Dairy",
        "default_unit": "kg",
        "aliases": ["paneer", "panir", "cottage cheese", "পনির"]
    }
}

CATEGORY_TRANSLATIONS = {
    "Produce": {"bn": "কাঁচা শাকসবজি (Produce)", "hi": "सब्जियां (Produce)"},
    "Dairy": {"bn": "দুগ্ধজাত পণ্য (Dairy)", "hi": "डेयरी उत्पाद (Dairy)"},
    "Poultry": {"bn": "হাঁস-মুরগি (Poultry)", "hi": "पोल्ट्री (Poultry)"},
    "Meat": {"bn": "মাংস (Meat)", "hi": "मांस (Meat)"},
    "Grains": {"bn": "শস্য ও চাল (Grains)", "hi": "अनाज (Grains)"},
    "Spices": {"bn": "মশলাপাতি (Spices)", "hi": "मसाले (Spices)"},
    "Pantry": {"bn": "প্যান্ট্রি / মুদিখানা (Pantry)", "hi": "पेंट्री (Pantry)"},
    "Beverages": {"bn": "পানীয় (Beverages)", "hi": "पेय पदार्थ (Beverages)"},
}

UNIT_TRANSLATIONS = {
    "kg": {"bn": "কেজি (kg)", "hi": "किलो (kg)"},
    "liters": {"bn": "লিটার (liters)", "hi": "लीटर (liters)"},
    "packets": {"bn": "প্যাকেট (packets)", "hi": "पैकेट (packets)"},
    "units": {"bn": "টি / একক (units)", "hi": "इकाई (units)"},
    "grams": {"bn": "গ্রাম (grams)", "hi": "ग्राम (grams)"},
    "cans": {"bn": "ক্যান (cans)", "hi": "कैन (cans)"},
    "boxes": {"bn": "বাক্স (boxes)", "hi": "डिब्बे (boxes)"},
}


# ----------------- Smart Typo Correction & Fuzzy Matching -----------------

def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate the Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


def normalize_item_name(raw_name: str) -> Dict[str, Any]:
    """
    Intelligently normalize item names handling spelling mistakes,
    Bengali/Hindi phonetic transliterations, and plurals.
    
    Returns a dictionary:
    {
        "canonical": str,         # Standardized English name, e.g. "Potatoes"
        "display_bn": str,        # Bengali meaning, e.g. "আলু (Alu)"
        "display_hi": str,        # Hindi meaning, e.g. "आलू (Aloo)"
        "category": str,          # Auto-inferred category, e.g. "Produce"
        "default_unit": str,      # Logical unit, e.g. "kg"
        "matched": bool           # Whether a lexicon match/fuzzy match occurred
    }
    """
    clean = re.sub(r"[^\w\s]", "", raw_name.lower().strip())
    tokens = clean.split()

    # 1. Exact or Alias matching
    for key, data in FOOD_ITEMS_LEXICON.items():
        for alias in data["aliases"]:
            # Check full match or substring match
            if clean == alias or alias in clean or any(t == alias for t in tokens):
                return {
                    "canonical": data["canonical"],
                    "display_bn": data["bn"],
                    "display_hi": data["hi"],
                    "category": data["category"],
                    "default_unit": data["default_unit"],
                    "matched": True,
                }

    # 2. Fuzzy Matching for Spelling Mistakes (Levenshtein Distance <= 2)
    best_match = None
    min_dist = float("inf")

    for key, data in FOOD_ITEMS_LEXICON.items():
        for alias in data["aliases"]:
            # Compare with the input or with individual words
            d_full = levenshtein_distance(clean, alias)
            if d_full < min_dist:
                min_dist = d_full
                best_match = data
            for token in tokens:
                d_tok = levenshtein_distance(token, alias)
                if d_tok < min_dist:
                    min_dist = d_tok
                    best_match = data

    # Threshold: tolerate up to 2 typos for medium words, 1 for short words
    max_tolerated = 2 if len(clean) >= 4 else 1
    if best_match and min_dist <= max_tolerated:
        return {
            "canonical": best_match["canonical"],
            "display_bn": best_match["bn"],
            "display_hi": best_match["hi"],
            "category": best_match["category"],
            "default_unit": best_match["default_unit"],
            "matched": True,
        }

    # 3. Fallback for unlisted/custom ingredients
    title_name = raw_name.strip().title()
    return {
        "canonical": title_name,
        "display_bn": f"{title_name} (কাস্টম আইটেম)",
        "display_hi": f"{title_name} (कस्टम आइटम)",
        "category": "Pantry",
        "default_unit": "units",
        "matched": False,
    }


def get_item_localized_display(canonical_name: str, lang: str = "en") -> str:
    """Return the localized name and meaning of a food item."""
    norm = normalize_item_name(canonical_name)
    if lang == "bn":
        return f"{norm['canonical']} — {norm['display_bn']}"
    elif lang == "hi":
        return f"{norm['canonical']} — {norm['display_hi']}"
    return norm["canonical"]


def get_category_localized(category: str, lang: str = "en") -> str:
    """Return localized category string."""
    cat_data = CATEGORY_TRANSLATIONS.get(category, {})
    if lang in ("bn", "hi"):
        return cat_data.get(lang, category)
    return category


def get_unit_localized(unit: str, lang: str = "en") -> str:
    """Return localized unit string."""
    unit_data = UNIT_TRANSLATIONS.get(unit.lower(), {})
    if lang in ("bn", "hi"):
        return unit_data.get(lang, unit)
    return unit
