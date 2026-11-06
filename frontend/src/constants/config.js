export const UNITS = ['kg', 'liters', 'units', 'grams', 'cans', 'boxes', 'packets']

export const CATEGORIES = [
  'Produce',
  'Dairy',
  'Poultry',
  'Meat',
  'Grains',
  'Spices',
  'Pantry',
  'Beverages',
]

export const ORDER_STATUSES = ['PROCESSING', 'IN_TRANSIT', 'DELIVERED', 'CANCELLED']

export const FALLBACK_TRANSLATIONS = {
  app_title: {
    en: '🍽️ HutMate AI',
    bn: '🍽️ হাটমেট এআই (HutMate AI)',
    hi: '🍽️ हटमेट एআই (HutMate AI)',
  },
  app_caption: {
    en: 'Intelligent Restaurant Operations Assistant — Production Hospitality Edition',
    bn: 'স্মার্ট রেস্তোরাঁ অপারেশন সহকারী — বহুভাষিক সংস্করণ',
    hi: 'स्मार्ट रेस्तरां संचालन सहायक — बहुभाषी संस्करण',
  },
  tab_chat: {
    en: '💬 Operations Chat',
    bn: '💬 অপারেশন চ্যাট',
    hi: '💬 संचालन चैट',
  },
  tab_data: {
    en: '📊 Live Restaurant Data',
    bn: '📊 লাইভ রেস্তোরাঁর তথ্য',
    hi: '📊 लाइव रेस्तरां डेटा',
  },
  tab_approvals: {
    en: '✅ Action Approvals',
    bn: '✅ অ্যাকশন অনুমোদন',
    hi: '✅ कार्रवाई अनुमोदन',
  },
  sidebar_sys_ops: {
    en: '⚙️ System Operations',
    bn: '⚙️ সিস্টেম সেটিংস ও অপারেশন',
    hi: '⚙️ सिस्टम संचालन',
  },
  btn_reseed: {
    en: '🔄 Reset / Seed Demo SQLite Data',
    bn: '🔄 ডেমো ডেটা রিসেট / পুনরায় লোড করুন',
    hi: '🔄 डेमो डेटा रीसेट / पुनः लोड करें',
  },
  btn_load_samples: {
    en: '📚 Index Built-in Sample Documents',
    bn: '📚 স্যাম্পল রেস্তোরাঁ নির্দেশিকা ইন্ডেক্স করুন',
    hi: '📚 नमूना दस्तावेज इंडेक्स करें',
  },
  sidebar_doc_upload: {
    en: '📄 Upload Restaurant Documents (RAG)',
    bn: '📄 রেস্তোরাঁর নথি আপলোড করুন (RAG)',
    hi: '📄 रेस्तरां दस्तावेज अपलोड करें (RAG)',
  },
  sidebar_doc_caption: {
    en: 'Upload menus, policies, or supplier guides (PDF, DOCX, TXT). HutMate AI will cite exact page numbers.',
    bn: 'মেনু, খাদ্য সুরক্ষা নির্দেশিকা বা সরবরাহকারী চুক্তি (PDF, DOCX, TXT) আপলোড করুন। এআই পৃষ্ঠার নম্বর সহ উত্তর দেবে।',
    hi: 'मेनू, नीतियां या आपूर्तिकर्ता गाइड अपलोड करें (PDF, DOCX, TXT)। एआई सटीक पृष्ठ संख्या बताएगा।',
  },
  btn_index_docs: {
    en: '📥 Index Uploaded Documents',
    bn: '📥 আপলোড করা নথি ইন্ডেক্স করুন',
    hi: '📥 अपलोड किए गए दस्तावेज इंडेक्स करें',
  },
  metric_chunks: {
    en: 'Total Indexed Knowledge Chunks',
    bn: 'মোট ইন্ডেক্স করা নথির অংশ (Chunks)',
    hi: 'कुल इंडेक्स किए गए ज्ञान खंड',
  },
  chat_heading: {
    en: 'Conversational Assistant',
    bn: 'কথোপকথন সহায়ক (AI Assistant)',
    hi: 'बातचीत सहायक',
  },
  chat_caption: {
    en: 'Ask questions about recipes, policies, stock, orders, or ask to draft a purchase order.',
    bn: 'রেসিপি, নীতি, বর্তমান স্টক, অর্ডার বা কেনাকাটার রিকুইজিশন তৈরি করতে যেকোনো প্রশ্ন জিজ্ঞাসা করুন।',
    hi: 'व्यंजनों, नीतियों, स्टॉक, ऑर्डर के बारे में प्रश्न पूछें, या खरीदारी का मसौदा तैयार करने को कहें।',
  },
  btn_clear_chat: {
    en: '🗑️ Clear Chat',
    bn: '🗑️ চ্যাট মুছুন',
    hi: '🗑️ चैट साफ़ करें',
  },
  chat_placeholder: {
    en: "Ask HutMate AI (e.g. 'How many Biryanis can we cook?' or 'Which items are low in stock?')",
    bn: "হাটমেট এআই-কে জিজ্ঞাসা করুন (যেমন 'কয় প্লেট বিরিয়ানি বানানো যাবে?' বা 'কোন উপাদান কম আছে?')",
    hi: "हटमेट एआई से पूछें (जैसे 'कितनी बिरयानी बनाई जा सकती है?' या 'कौन से आइटम कम हैं?')",
  },
  welcome_message: {
    en: 'Hello! I am HutMate AI, your restaurant operations assistant. How can I assist you today?',
    bn: 'নমস্কার! আমি হাটমেট এআই (HutMate AI), আপনার রেস্তোরাঁ অপারেশন সহকারী। আজ আপনাকে কীভাবে সাহায্য করতে পারি?',
    hi: 'नमस्ते! मैं हटमेट एआई (HutMate AI) हूं, आपका रेस्तरां संचालन सहायक। आज मैं आपकी क्या सहायता कर सकता हूँ?',
  },
  subtab_inventory: {
    en: '📦 Inventory Items',
    bn: '📦 ইনভেন্টরি পণ্য (স্টক)',
    hi: '📦 इन्वेंटरी आइटम',
  },
  subtab_recipes: {
    en: '🍳 Kitchen Recipes & BOM',
    bn: '🍳 রান্নাঘরের রেসিপি ও BOM',
    hi: '🍳 रसोई रेसिपी व सामग्री',
  },
  subtab_suppliers: {
    en: '🚚 Suppliers',
    bn: '🚚 সরবরাহকারী তালিকা (Suppliers)',
    hi: '🚚 आपूर्तिकर्ता',
  },
  subtab_orders: {
    en: '📋 Orders',
    bn: '📋 অর্ডার সমূহ',
    hi: '📋 অর্ডার',
  },
  btn_save_inv: {
    en: '💾 Save Inventory Changes',
    bn: '💾 ইনভেন্টরির পরিবর্তন সংরক্ষণ করুন',
    hi: '💾 इन्वेंटरी परिवर्तन सहेजें',
  },
  btn_save_sup: {
    en: '💾 Save Supplier Changes',
    bn: '💾 সরবরাহকারী তথ্য সংরক্ষণ করুন',
    hi: '💾 आपूर्तिकर्ता परिवर्तन सहेजें',
  },
  btn_save_ord: {
    en: '💾 Save Orders Changes',
    bn: '💾 অর্ডারের পরিবর্তন সংরক্ষণ করুন',
    hi: '💾 ऑर्डर परिवर्तन सहेजें',
  },
  subtab_pending: {
    en: '⏳ Pending Approvals Queue',
    bn: '⏳ অনুমোদনের অপেক্ষমাণ তালিকা',
    hi: '⏳ लंबित अनुमोदन कतार',
  },
  subtab_history: {
    en: '📜 Approval History & Audit Trail',
    bn: '📜 অনুমোদনের ইতিহাস ও অডিট লগ',
    hi: '📜 अनुमोदन इतिहास और ऑडिट लॉग',
  },
  btn_approve: {
    en: '✅ Approve',
    bn: '✅ অনুমোদন করুন',
    hi: '✅ स्वीकृत करें',
  },
  btn_reject: {
    en: '❌ Reject',
    bn: '❌ বাতিল করুন',
    hi: '❌ अस्वीकृत करें',
  },
}

export const DEMO_PROMPTS = [
  'How many portions of Dum Chicken Biryani can we cook right now?',
  'Which items are currently below minimum par levels?',
  'We just sold 6 plates of Dum Chicken Biryani, deduct from stock.',
  'আমাদের কাছে কি আলু বা পনির আছে?',
  'What is our food storage temperature policy?',
  'Prepare a purchase request for 25 kg of Basmati Rice from Golden Grain Traders.',
]
