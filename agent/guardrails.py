import re
from typing import Dict, Any, Tuple, Optional

# Prompt Injection & Jailbreak patterns
RE_JAILBREAK = re.compile(
    r"(?:ignore\s+all\s+(?:previous|prior)\s+instructions)|"
    r"(?:disregard\s+(?:all\s+)?instructions)|"
    r"(?:you\s+are\s+now\s+(?:DAN|unrestricted|jailbroken))|"
    r"(?:bypass\s+(?:all\s+)?(?:safety|content|security)\s+filters)|"
    r"(?:act\s+as\s+an\s+unfiltered\s+ai)",
    re.IGNORECASE,
)

# Out-of-domain keywords (unrelated to restaurant/hospitality operations)
OUT_OF_DOMAIN_PATTERNS = [
    re.compile(r"\b(?:python|javascript|c\+\+|java|rust|html|css)\s+(?:code|script|program|app|compiler)\b", re.IGNORECASE),
    re.compile(r"\b(?:hack|exploit|ddos|sql\s+injection|malware|keylogger|phishing)\b", re.IGNORECASE),
    re.compile(r"\b(?:capital\s+of\s+[a-z]+|who\s+won\s+the\s+(?:world\s+cup|super\s+bowl|election))\b", re.IGNORECASE),
    re.compile(r"\b(?:cryptocurrency|bitcoin|ethereum|forex\s+trading|stock\s+market\s+prediction)\b", re.IGNORECASE),
    re.compile(r"\b(?:quantum\s+physics|relativity\s+theory|astrophysics)\b", re.IGNORECASE),
]

# In-domain restaurant operations keywords
IN_DOMAIN_KEYWORDS = {
    # Food & Ingredients
    "chicken", "rice", "biryani", "oil", "onions", "tomatoes", "masala", "yogurt", "cheese", "paneer",
    "flour", "atta", "butter", "garlic", "ginger", "potato", "potatoes", "meat", "poultry", "dairy",
    "produce", "spices", "grains", "food", "ingredient", "ingredients", "curry", "naan", "roti",
    "alu", "aloo", "murgi", "dim", "mach", "peyaj", "pyaz", "tamatar", "doodh", "chawal", "bhaat",
    # Kitchen & Operations
    "inventory", "stock", "par", "level", "levels", "par_level", "low_stock", "shortage", "shortages",
    "reorder", "supplier", "suppliers", "order", "orders", "purchase", "request", "draft", "approve",
    "recipe", "recipes", "feasibility", "portion", "portions", "plate", "plates", "servings",
    "cook", "cooked", "prepare", "prepared", "sell", "sold", "sales", "kitchen", "chef", "cooks",
    "cost", "price", "expiry", "expire", "hygiene", "sop", "policy", "storage", "temperature",
    # Chat / Conversational
    "hello", "hi", "hey", "help", "thank", "thanks", "bengali", "hindi", "english", "speak", "status",
    "menu", "what", "how", "show", "list", "check", "add", "delete", "update", "deduct", "koro", "bolo"
}

DEFLECTION_MESSAGES = {
    "en": (
        "🍽️ I am **HutMate AI**, specialized in restaurant operations, kitchen recipes, "
        "inventory tracking, supplier coordination, and food safety standards. "
        "I cannot assist with topics outside restaurant management. "
        "How can I help with your kitchen, recipes, or inventory today?"
    ),
    "bn": (
        "🍽️ আমি **হাটমেট এআই (HutMate AI)**, শুধুমাত্র রেস্তোরাঁ পরিচালনা, রান্নাঘরের রেসিপি, "
        "ইনভেন্টরি পর্যবেক্ষণ, সরবরাহকারী সমন্বয় এবং খাদ্য সুরক্ষা মানদণ্ডের জন্য বিশেষভাবে তৈরি। "
        "রেস্তোরাঁ-বহির্ভূত বিষয়ে আমি সাহায্য করতে পারি না। "
        "আজ আপনার রেস্তোরাঁর ইনভেন্টরি বা রেসিপি সংক্রান্ত কাজে আমি কীভাবে সাহায্য করতে পারি?"
    ),
    "hi": (
        "🍽️ मैं **हटमेट एआई (HutMate AI)** हूँ, विशेष रूप से रेस्तरां संचालन, किचन रेसिपी, "
        "इन्वेंट्री ट्रैकिंग, आपूर्तिकर्ता समन्वय और खाद्य सुरक्षा मानकों के लिए डिज़ाइन किया गया हूँ। "
        "मैं रेस्तरां प्रबंधन से असंबंधित विषयों पर सहायता नहीं कर सकता। "
        "आज आपके रेस्तरां किचन या इन्वेंट्री में क्या मदद कर सकता हूँ?"
    ),
}

def inspect_guardrails(prompt: str, language: str = "en") -> Tuple[bool, Optional[str]]:
    """
    Check if the user prompt violates enterprise restaurant domain guardrails.
    Returns (is_blocked: bool, deflection_message: Optional[str]).
    """
    if not prompt or not prompt.strip():
        return False, None

    text = prompt.strip()

    # 1. Prompt Injection / Jailbreak Guardrail
    if RE_JAILBREAK.search(text):
        lang = language if language in DEFLECTION_MESSAGES else "en"
        return True, DEFLECTION_MESSAGES[lang]

    # 2. Out-of-Domain Pattern Match
    for pattern in OUT_OF_DOMAIN_PATTERNS:
        if pattern.search(text):
            lang = language if language in DEFLECTION_MESSAGES else "en"
            return True, DEFLECTION_MESSAGES[lang]

    # 3. Keyword Domain Density Check (only for queries longer than 5 words)
    words = re.findall(r"\w+", text.lower())
    if len(words) >= 6:
        domain_matches = sum(1 for w in words if w in IN_DOMAIN_KEYWORDS)
        # If a long query has zero domain-relevant words, check if it's completely alien
        if domain_matches == 0:
            # Allow common short greetings or questions, otherwise flag as out-of-domain
            alien_words = {"president", "physics", "galaxies", "cryptocurrency", "blockchain", "football", "cricket", "hollywood", "actor"}
            if any(w in words for w in alien_words):
                lang = language if language in DEFLECTION_MESSAGES else "en"
                return True, DEFLECTION_MESSAGES[lang]

    return False, None
