import React, { useState, useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

const UNITS = ['kg', 'liters', 'units', 'grams', 'cans', 'boxes', 'packets']
const CATEGORIES = [
  'Produce',
  'Dairy',
  'Poultry',
  'Meat',
  'Grains',
  'Spices',
  'Pantry',
  'Beverages',
]
const ORDER_STATUSES = ['PROCESSING', 'IN_TRANSIT', 'DELIVERED', 'CANCELLED']

const FALLBACK_TRANSLATIONS = {
  app_title: {
    en: '🍽️ HutMate AI',
    bn: '🍽️ হাটমেট এআই (HutMate AI)',
    hi: '🍽️ हटमेट एआई (HutMate AI)',
  },
  app_caption: {
    en: 'Intelligent Restaurant Operations Assistant — Multilingual Edition',
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
    en: "Ask HutMate AI (e.g. 'How much chicken is in stock?' or 'Do we have cheese?')",
    bn: "হাটমেট এআই-কে জিজ্ঞাসা করুন (যেমন 'স্টকে কতটা মুরগির মাংস আছে?' বা 'আমাদের কি আলু আছে?')",
    hi: "हटमेट एआई से पूछें (जैसे 'स्टॉक में कितना चिकन है?' या 'क्या हमारे पास आलू है?')",
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
  subtab_suppliers: {
    en: '🚚 Suppliers',
    bn: '🚚 সরবরাহকারী তালিকা (Suppliers)',
    hi: '🚚 आपूर्तिकर्ता',
  },
  subtab_orders: {
    en: '📋 Orders',
    bn: '📋 অর্ডার সমূহ',
    hi: '📋 ऑर्डर',
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

const DEMO_PROMPTS = [
  'What is our food storage policy?',
  'Do you have cheese?',
  'আমাদের কাছে কি আলু আছে?',
  '৫ প্যাকেট চিজ যোগ করুন',
  'What is the status of order ORD-1001?',
  'Prepare a purchase request for 25 kg of Basmati Rice from Golden Grain Traders.',
]

export default function App() {
  const [lang, setLang] = useState('en')
  const [translations, setTranslations] = useState(FALLBACK_TRANSLATIONS)
  const [activeTab, setActiveTab] = useState('chat')
  const [dataSubTab, setDataSubTab] = useState('inventory')
  const [approvalSubTab, setApprovalSubTab] = useState('pending')

  // App state from backend
  const [indexedChunks, setIndexedChunks] = useState(0)
  const [inventory, setInventory] = useState([])
  const [suppliers, setSuppliers] = useState([])
  const [orders, setOrders] = useState([])
  const [pendingRequests, setPendingRequests] = useState([])
  const [allRequests, setAllRequests] = useState([])

  // Toast feedback
  const [toast, setToast] = useState(null)
  const showToast = (message, type = 'success') => {
    setToast({ message, type })
    setTimeout(() => {
      setToast((prev) => (prev?.message === message ? null : prev))
    }, 4500)
  }

  // Translation helper matching core.i18n.t()
  const t = (key, targetLang = lang) => {
    const dict = translations[key] || FALLBACK_TRANSLATIONS[key] || {}
    return dict[targetLang] || dict.en || key
  }

  // Chat state
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: FALLBACK_TRANSLATIONS.welcome_message.en,
    },
  ])
  const [chatInput, setChatInput] = useState('')
  const [isChatLoading, setIsChatLoading] = useState(false)
  const chatEndRef = useRef(null)

  // Sidebar operations loading states
  const [isReseeding, setIsReseeding] = useState(false)
  const [isIndexingSamples, setIsIndexingSamples] = useState(false)
  const [selectedFiles, setSelectedFiles] = useState([])
  const [isUploadingDocs, setIsUploadingDocs] = useState(false)
  const fileInputRef = useRef(null)

  // Quick Add Forms State
  const [newInv, setNewInv] = useState({
    item_name: '',
    quantity: 10.0,
    unit: 'kg',
    category: 'Produce',
  })
  const [newSup, setNewSup] = useState({
    name: '',
    contact_person: '',
    phone: '',
    email: '',
    supplied_categories: '',
  })
  const [newOrd, setNewOrd] = useState({
    order_number: '',
    item_name: '',
    quantity: 20.0,
    unit: 'kg',
    supplier_name: '',
    status: 'PROCESSING',
  })
  const [manualDraft, setManualDraft] = useState({
    item_name: '',
    quantity: 25.0,
    unit: 'kg',
    supplier_name: '',
  })

  // Apply backend state snapshot
  const applyBackendState = (state) => {
    if (!state) return
    if (state.translations) setTranslations(state.translations)
    if (typeof state.indexed_chunks === 'number') setIndexedChunks(state.indexed_chunks)
    if (Array.isArray(state.inventory)) setInventory(state.inventory)
    if (Array.isArray(state.suppliers)) setSuppliers(state.suppliers)
    if (Array.isArray(state.orders)) setOrders(state.orders)
    if (Array.isArray(state.pending_requests)) setPendingRequests(state.pending_requests)
    if (Array.isArray(state.all_requests)) setAllRequests(state.all_requests)
  }

  // Initial bootstrap fetch
  useEffect(() => {
    fetch('/api/bootstrap')
      .then((res) => res.json())
      .then((data) => {
        applyBackendState(data)
      })
      .catch((err) => {
        showToast(`Failed to connect to backend API: ${err.message}`, 'error')
      })
  }, [])

  // Auto-scroll chat feed
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isChatLoading])

  // Handle language change from Sidebar
  const handleLanguageChange = (newLang) => {
    setLang(newLang)
    setMessages((prev) => {
      if (prev.length === 1 && prev[0].role === 'assistant') {
        return [{ role: 'assistant', content: t('welcome_message', newLang) }]
      }
      return prev
    })
  }

  // Sidebar: Reseed demo database
  const handleReseed = async () => {
    setIsReseeding(true)
    try {
      const res = await fetch('/api/system/reseed', { method: 'POST' })
      const data = await res.json()
      applyBackendState(data.state)
      showToast(
        lang === 'en'
          ? 'Sample database reseeded!'
          : 'ডেমো ডেটা সফলভাবে লোড হয়েছে!',
        'success'
      )
    } catch (err) {
      showToast(`Error reseeding database: ${err.message}`, 'error')
    } finally {
      setIsReseeding(false)
    }
  }

  // Sidebar: Index built-in sample documents
  const handleLoadSamples = async () => {
    setIsIndexingSamples(true)
    try {
      const res = await fetch('/api/rag/load-samples', { method: 'POST' })
      const data = await res.json()
      setIndexedChunks(data.total_indexed_chunks)
      showToast(
        lang === 'en'
          ? `Indexed ${data.chunks_indexed} chunk(s)!`
          : `${data.chunks_indexed} টি অংশ ইন্ডেক্স করা হয়েছে!`,
        'success'
      )
    } catch (err) {
      showToast(`Error indexing sample documents: ${err.message}`, 'error')
    } finally {
      setIsIndexingSamples(false)
    }
  }

  // Sidebar: Upload & Index user documents
  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files || [])
    if (files.length > 0) {
      setSelectedFiles((prev) => [...prev, ...files])
    }
  }

  const handleRemoveSelectedFile = (idx) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== idx))
  }

  const handleIndexUploadedDocs = async () => {
    if (selectedFiles.length === 0) return
    setIsUploadingDocs(true)
    try {
      const formData = new FormData()
      selectedFiles.forEach((f) => formData.append('files', f))
      const res = await fetch('/api/rag/upload', {
        method: 'POST',
        body: formData,
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Upload failed')
      setIndexedChunks(data.total_indexed_chunks)
      setSelectedFiles([])
      if (fileInputRef.current) fileInputRef.current.value = ''
      showToast(
        `Successfully indexed ${data.chunks_indexed} chunk(s) into ChromaDB!`,
        'success'
      )
    } catch (err) {
      showToast(`Upload error: ${err.message}`, 'error')
    } finally {
      setIsUploadingDocs(false)
    }
  }

  // Tab 1: Operations Chat submission
  const sendChatMessage = async (promptText) => {
    const trimmed = (promptText ?? chatInput).trim()
    if (!trimmed || isChatLoading) return

    const updatedHistory = [...messages, { role: 'user', content: trimmed }]
    setMessages(updatedHistory)
    setChatInput('')
    setIsChatLoading(true)

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: trimmed,
          history: messages.map((m) => ({ role: m.role, content: m.content })),
          language: lang,
        }),
      })
      const data = await res.json()
      if (data.active_language && data.active_language !== lang) {
        setLang(data.active_language)
      }
      if (data.state) {
        applyBackendState(data.state)
      }
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: data.answer || 'No response generated.',
          sources: data.sources || [],
          tools_used: data.tools_used || [],
        },
      ])
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `⚠️ Error: ${err.message}`,
        },
      ])
    } finally {
      setIsChatLoading(false)
    }
  }

  const handleClearChat = () => {
    setMessages([{ role: 'assistant', content: t('welcome_message', lang) }])
  }

  // Tab 2: Inventory Handlers
  const handleInventoryCellChange = (index, field, value) => {
    setInventory((prev) =>
      prev.map((row, i) => (i === index ? { ...row, [field]: value } : row))
    )
  }

  const handleAddInventoryRow = () => {
    setInventory((prev) => [
      ...prev,
      {
        item_name: '',
        display_bn: '',
        display_hi: '',
        quantity: 1.0,
        unit: 'kg',
        category: 'Produce',
      },
    ])
  }

  const handleDeleteInventoryRow = (index) => {
    setInventory((prev) => prev.filter((_, i) => i !== index))
  }

  const handleSaveInventoryTable = async () => {
    try {
      const validItems = inventory
        .filter((r) => r.item_name && r.item_name.trim())
        .map((r) => ({
          item_name: r.item_name.trim(),
          quantity: parseFloat(r.quantity) || 0,
          unit: r.unit || 'kg',
          category: r.category || 'Pantry',
        }))
      const res = await fetch('/api/inventory/sync', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ items: validItems }),
      })
      const data = await res.json()
      if (data.inventory) setInventory(data.inventory)
      showToast(
        lang === 'en'
          ? '✅ Inventory updated successfully in SQLite database!'
          : '✅ ইনভেন্টরি সফলভাবে আপডেট করা হয়েছে!',
        'success'
      )
    } catch (err) {
      showToast(`Failed to save inventory: ${err.message}`, 'error')
    }
  }

  const handleQuickAddInventory = async (e) => {
    e.preventDefault()
    if (!newInv.item_name.trim()) return
    try {
      const res = await fetch('/api/inventory', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          item_name: newInv.item_name,
          quantity: parseFloat(newInv.quantity) || 0,
          unit: newInv.unit,
          category: newInv.category,
        }),
      })
      const data = await res.json()
      if (data.inventory) setInventory(data.inventory)
      setNewInv({ ...newInv, item_name: '' })
      showToast(
        `Added: ${data.result?.item_name || newInv.item_name} (${data.result?.display_bn || ''})!`,
        'success'
      )
    } catch (err) {
      showToast(`Error adding item: ${err.message}`, 'error')
    }
  }

  // Tab 2: Suppliers Handlers
  const handleSupplierCellChange = (index, field, value) => {
    setSuppliers((prev) =>
      prev.map((row, i) => (i === index ? { ...row, [field]: value } : row))
    )
  }

  const handleAddSupplierRow = () => {
    setSuppliers((prev) => [
      ...prev,
      {
        name: '',
        contact_person: '',
        phone: '',
        email: '',
        supplied_categories: '',
      },
    ])
  }

  const handleDeleteSupplierRow = (index) => {
    setSuppliers((prev) => prev.filter((_, i) => i !== index))
  }

  const handleSaveSuppliersTable = async () => {
    try {
      const validSuppliers = suppliers
        .filter((s) => s.name && s.name.trim())
        .map((s) => ({
          name: s.name.trim(),
          contact_person: s.contact_person || '',
          phone: s.phone || '',
          email: s.email || '',
          supplied_categories: s.supplied_categories || '',
        }))
      const res = await fetch('/api/suppliers/sync', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ items: validSuppliers }),
      })
      const data = await res.json()
      if (data.suppliers) setSuppliers(data.suppliers)
      showToast(
        lang === 'en'
          ? '✅ Supplier directory updated successfully in SQLite!'
          : '✅ সরবরাহকারী তথ্য সফলভাবে আপডেট হয়েছে!',
        'success'
      )
    } catch (err) {
      showToast(`Failed to save suppliers: ${err.message}`, 'error')
    }
  }

  const handleQuickAddSupplier = async (e) => {
    e.preventDefault()
    if (!newSup.name.trim()) return
    try {
      const res = await fetch('/api/suppliers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newSup),
      })
      const data = await res.json()
      if (data.suppliers) setSuppliers(data.suppliers)
      showToast(`Added ${newSup.name} to suppliers!`, 'success')
      setNewSup({
        name: '',
        contact_person: '',
        phone: '',
        email: '',
        supplied_categories: '',
      })
    } catch (err) {
      showToast(`Error adding supplier: ${err.message}`, 'error')
    }
  }

  // Tab 2: Orders Handlers
  const handleOrderCellChange = (index, field, value) => {
    setOrders((prev) =>
      prev.map((row, i) => (i === index ? { ...row, [field]: value } : row))
    )
  }

  const handleAddOrderRow = () => {
    setOrders((prev) => [
      ...prev,
      {
        order_number: `ORD-${1000 + prev.length + 1}`,
        item_name: '',
        quantity: 10.0,
        unit: 'kg',
        supplier_name: '',
        status: 'PROCESSING',
      },
    ])
  }

  const handleDeleteOrderRow = (index) => {
    setOrders((prev) => prev.filter((_, i) => i !== index))
  }

  const handleSaveOrdersTable = async () => {
    try {
      const validOrders = orders
        .filter((o) => o.order_number && o.order_number.trim() && o.item_name && o.item_name.trim())
        .map((o) => ({
          order_number: o.order_number.trim(),
          item_name: o.item_name.trim(),
          quantity: parseFloat(o.quantity) || 0,
          unit: o.unit || 'kg',
          supplier_name: o.supplier_name || '',
          status: o.status || 'PROCESSING',
        }))
      const res = await fetch('/api/orders/sync', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ items: validOrders }),
      })
      const data = await res.json()
      if (data.orders) setOrders(data.orders)
      showToast(
        lang === 'en'
          ? '✅ Order records updated successfully in SQLite!'
          : '✅ অর্ডারের তথ্য সফলভাবে আপডেট হয়েছে!',
        'success'
      )
    } catch (err) {
      showToast(`Failed to save orders: ${err.message}`, 'error')
    }
  }

  const handleQuickAddOrder = async (e) => {
    e.preventDefault()
    if (!newOrd.order_number.trim() || !newOrd.item_name.trim()) return
    try {
      const res = await fetch('/api/orders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...newOrd,
          quantity: parseFloat(newOrd.quantity) || 1.0,
        }),
      })
      const data = await res.json()
      if (data.orders) setOrders(data.orders)
      showToast(`Recorded order ${newOrd.order_number}!`, 'success')
      setNewOrd({
        order_number: '',
        item_name: '',
        quantity: 20.0,
        unit: 'kg',
        supplier_name: '',
        status: 'PROCESSING',
      })
    } catch (err) {
      showToast(`Error recording order: ${err.message}`, 'error')
    }
  }

  // Tab 3: Action Approvals Handlers
  const handleResolveRequest = async (reqId, decision) => {
    try {
      const res = await fetch(`/api/approvals/${reqId}/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ decision }),
      })
      const data = await res.json()
      if (data.state) applyBackendState(data.state)
      if (decision === 'APPROVED') {
        showToast(
          lang === 'en'
            ? `Request #${reqId} Approved! Stock updated and order placed.`
            : `রিকোয়েস্ট #${reqId} অনুমোদিত! স্টক আপডেট হয়েছে।`,
          'success'
        )
      } else {
        showToast(
          lang === 'en'
            ? `Request #${reqId} Rejected.`
            : `রিকোয়েস্ট #${reqId} বাতিল করা হয়েছে।`,
          'warning'
        )
      }
    } catch (err) {
      showToast(`Error resolving request: ${err.message}`, 'error')
    }
  }

  const handleManualDraftSubmit = async (e) => {
    e.preventDefault()
    if (!manualDraft.item_name.trim() || !manualDraft.supplier_name.trim()) return
    try {
      const res = await fetch('/api/approvals', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...manualDraft,
          quantity: parseFloat(manualDraft.quantity) || 1.0,
        }),
      })
      const data = await res.json()
      if (data.pending_requests) setPendingRequests(data.pending_requests)
      if (data.all_requests) setAllRequests(data.all_requests)
      showToast(
        `Created draft purchase request for ${manualDraft.quantity} ${manualDraft.unit} ${manualDraft.item_name}!`,
        'success'
      )
      setManualDraft({
        item_name: '',
        quantity: 25.0,
        unit: 'kg',
        supplier_name: '',
      })
    } catch (err) {
      showToast(`Error drafting request: ${err.message}`, 'error')
    }
  }

  const meaningColumnHeader =
    lang === 'bn'
      ? 'Local Meaning (বাংলা অর্থ)'
      : lang === 'hi'
        ? 'स्थानीय अर्थ (Hindi)'
        : 'Local Meaning'

  const thinkingText =
    lang === 'en'
      ? 'HutMate AI is thinking and consulting operational tools...'
      : lang === 'bn'
        ? 'হাটমেট এআই তথ্য বিশ্লেষণ করছে...'
        : 'हटमेट एआई जानकारी का विश्लेषण कर रहा है...'

  return (
    <div className="app-shell">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-brand-icon">🍽️</div>
          <div>
            <h2>HutMate AI</h2>
            <span>Restaurant Operations Copilot</span>
          </div>
        </div>

        {/* Language Selector */}
        <div className="sidebar-section">
          <div className="sidebar-section-title">
            🌐 {lang === 'bn' ? 'Language / ভাষা' : 'Language / भाषा / ভাষা'}
          </div>
          <select
            className="sidebar-select"
            value={lang}
            onChange={(e) => handleLanguageChange(e.target.value)}
            aria-label="System Language"
          >
            <option value="en">🇬🇧 English</option>
            <option value="bn">🇧🇩 বাংলা (Bengali)</option>
            <option value="hi">🇮🇳 हिंदी (Hindi)</option>
          </select>
        </div>

        {/* System Operations */}
        <div className="sidebar-section">
          <div className="sidebar-section-title">{t('sidebar_sys_ops')}</div>
          <button
            className="sidebar-btn"
            onClick={handleReseed}
            disabled={isReseeding}
          >
            {isReseeding ? '⏳ Resetting...' : t('btn_reseed')}
          </button>
          <button
            className="sidebar-btn"
            onClick={handleLoadSamples}
            disabled={isIndexingSamples}
          >
            {isIndexingSamples
              ? lang === 'en'
                ? '⏳ Indexing sample documents...'
                : '⏳ স্যাম্পল নির্দেশিকা ইন্ডেক্স করা হচ্ছে...'
              : t('btn_load_samples')}
          </button>
        </div>

        {/* Document Upload (RAG) */}
        <div className="sidebar-section">
          <div className="sidebar-section-title">{t('sidebar_doc_upload')}</div>
          <p className="sidebar-caption">{t('sidebar_doc_caption')}</p>

          <label className="upload-dropzone">
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.txt"
              multiple
              onChange={handleFileSelect}
            />
            <div style={{ fontSize: '1.3rem', marginBottom: '4px' }}>📂</div>
            <div style={{ fontSize: '0.82rem', color: '#e2e8f0', fontWeight: 600 }}>
              Click to select PDF, DOCX, TXT
            </div>
            <div style={{ fontSize: '0.73rem', color: '#94a3b8' }}>
              Multiple files supported
            </div>
          </label>

          {selectedFiles.length > 0 && (
            <div className="file-list">
              {selectedFiles.map((file, i) => (
                <div key={`${file.name}-${i}`} className="file-pill">
                  <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    📄 {file.name}
                  </span>
                  <button
                    type="button"
                    onClick={() => handleRemoveSelectedFile(i)}
                    title="Remove file"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          )}

          {selectedFiles.length > 0 && (
            <button
              className="sidebar-btn primary"
              onClick={handleIndexUploadedDocs}
              disabled={isUploadingDocs}
            >
              {isUploadingDocs
                ? '⏳ Processing & generating FastEmbed vectors...'
                : t('btn_index_docs')}
            </button>
          )}
        </div>

        {/* Total Indexed Chunks Metric */}
        <div className="metric-card">
          <span className="metric-label">{t('metric_chunks')}</span>
          <span className="metric-value">{indexedChunks}</span>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="main-workspace">
        {/* Header */}
        <header className="top-header">
          <div>
            <h1>{t('app_title')}</h1>
            <p>{t('app_caption')}</p>
          </div>
        </header>

        {/* Toast Banner */}
        {toast && (
          <div className={`toast-banner ${toast.type}`}>
            <span>{toast.message}</span>
            <button className="toast-close" onClick={() => setToast(null)}>
              ✕
            </button>
          </div>
        )}

        {/* Main Navigation Tabs */}
        <nav className="tabs-nav" role="tablist">
          <button
            role="tab"
            aria-selected={activeTab === 'chat'}
            className={`tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
          >
            {t('tab_chat')}
          </button>
          <button
            role="tab"
            aria-selected={activeTab === 'data'}
            className={`tab-btn ${activeTab === 'data' ? 'active' : ''}`}
            onClick={() => setActiveTab('data')}
          >
            {t('tab_data')}
            <span className="tab-badge">{inventory.length}</span>
          </button>
          <button
            role="tab"
            aria-selected={activeTab === 'approvals'}
            className={`tab-btn ${activeTab === 'approvals' ? 'active' : ''}`}
            onClick={() => setActiveTab('approvals')}
          >
            {t('tab_approvals')}
            {pendingRequests.length > 0 && (
              <span className="tab-badge urgent">{pendingRequests.length}</span>
            )}
          </button>
        </nav>

        {/* ================= TAB 1: OPERATIONS CHAT ================= */}
        {activeTab === 'chat' && (
          <section className="chat-wrapper">
            <div className="chat-top-bar">
              <div>
                <h3 style={{ fontSize: '1.08rem', fontWeight: 700 }}>
                  {t('chat_heading')}
                </h3>
                <p style={{ fontSize: '0.82rem', color: '#64748b' }}>
                  {t('chat_caption')}
                </p>
              </div>
              <button className="btn btn-secondary" onClick={handleClearChat}>
                {t('btn_clear_chat')}
              </button>
            </div>

            <div className="chat-feed">
              {messages.map((msg, idx) => (
                <div key={idx} className={`chat-msg ${msg.role}`}>
                  <div className="chat-avatar">
                    {msg.role === 'user' ? '🧑‍🍳' : '🤖'}
                  </div>
                  <div className="chat-bubble">
                    <div className="chat-text">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {msg.content}
                      </ReactMarkdown>
                    </div>

                    {msg.tools_used && msg.tools_used.length > 0 && (
                      <details className="tools-details">
                        <summary>
                          🛠️{' '}
                          {lang === 'en'
                            ? `Operational Tools Invoked (${msg.tools_used.length})`
                            : `ব্যবহৃত অপারেশনাল টুলস (${msg.tools_used.length})`}
                        </summary>
                        <pre>{JSON.stringify(msg.tools_used, null, 2)}</pre>
                      </details>
                    )}

                    {msg.sources && msg.sources.length > 0 && (
                      <div className="sources-row">
                        <span>📚 Sources:</span>
                        {Array.from(new Set(msg.sources)).map((src, sIdx) => (
                          <span key={sIdx} className="source-pill">
                            {src}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {isChatLoading && (
                <div className="chat-msg assistant">
                  <div className="chat-avatar">🤖</div>
                  <div className="chat-bubble">
                    <div className="chat-text" style={{ color: '#64748b', fontStyle: 'italic' }}>
                      ⏳ {thinkingText}
                    </div>
                  </div>
                </div>
              )}

              <div ref={chatEndRef} />
            </div>

            {/* Quick Try Prompts */}
            <div className="prompt-chips">
              {DEMO_PROMPTS.map((sample, idx) => (
                <button
                  key={idx}
                  type="button"
                  className="prompt-chip"
                  onClick={() => sendChatMessage(sample)}
                  disabled={isChatLoading}
                >
                  {sample}
                </button>
              ))}
            </div>

            {/* Chat Input Bar */}
            <form
              className="chat-input-bar"
              onSubmit={(e) => {
                e.preventDefault()
                sendChatMessage()
              }}
            >
              <input
                type="text"
                className="chat-input"
                placeholder={t('chat_placeholder')}
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                disabled={isChatLoading}
              />
              <button
                type="submit"
                className="btn btn-primary"
                disabled={isChatLoading || !chatInput.trim()}
              >
                {lang === 'en' ? 'Send ➤' : lang === 'bn' ? 'পাঠান ➤' : 'भेजें ➤'}
              </button>
            </form>
          </section>
        )}

        {/* ================= TAB 2: LIVE RESTAURANT DATA ================= */}
        {activeTab === 'data' && (
          <section className="panel-card">
            <div className="panel-header">
              <div>
                <h3>{t('tab_data')}</h3>
                <p>
                  {lang === 'en'
                    ? 'Inspect, edit values in-place, add new items, or delete records directly in the SQLite operational database.'
                    : 'লাইভ ডেটাবেসে পণ্যের পরিমাণ পরিবর্তন করুন, নতুন খাদ্য উপাদান যোগ করুন বা মুছে ফেলুন।'}
                </p>
              </div>

              <div className="subtabs-nav">
                <button
                  className={`subtab-btn ${dataSubTab === 'inventory' ? 'active' : ''}`}
                  onClick={() => setDataSubTab('inventory')}
                >
                  {t('subtab_inventory')} ({inventory.length})
                </button>
                <button
                  className={`subtab-btn ${dataSubTab === 'suppliers' ? 'active' : ''}`}
                  onClick={() => setDataSubTab('suppliers')}
                >
                  {t('subtab_suppliers')} ({suppliers.length})
                </button>
                <button
                  className={`subtab-btn ${dataSubTab === 'orders' ? 'active' : ''}`}
                  onClick={() => setDataSubTab('orders')}
                >
                  {t('subtab_orders')} ({orders.length})
                </button>
              </div>
            </div>

            {/* --- Subtab 1: Inventory --- */}
            {dataSubTab === 'inventory' && (
              <>
                <h4 style={{ fontSize: '1rem', fontWeight: 700 }}>
                  {lang === 'en' ? 'Inventory Stock Levels' : 'বর্তমান খাদ্যদ্রব্যের স্টক'}
                </h4>

                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Item Name / খাদ্যদ্রব্য</th>
                        <th>{meaningColumnHeader}</th>
                        <th>Quantity / পরিমাণ</th>
                        <th>Unit / একক</th>
                        <th>Category / বিভাগ</th>
                        <th style={{ width: '60px' }}></th>
                      </tr>
                    </thead>
                    <tbody>
                      {inventory.map((row, idx) => (
                        <tr key={row.id || idx}>
                          <td>
                            <input
                              type="text"
                              className="cell-input"
                              value={row.item_name}
                              placeholder="Item name..."
                              onChange={(e) =>
                                handleInventoryCellChange(idx, 'item_name', e.target.value)
                              }
                            />
                          </td>
                          <td>
                            <span className="cell-readonly">
                              {lang === 'hi'
                                ? row.display_hi || row.display_bn || '—'
                                : row.display_bn || '—'}
                            </span>
                          </td>
                          <td style={{ maxWidth: '130px' }}>
                            <input
                              type="number"
                              step="0.5"
                              min="0"
                              className="cell-input"
                              value={row.quantity}
                              onChange={(e) =>
                                handleInventoryCellChange(idx, 'quantity', e.target.value)
                              }
                            />
                          </td>
                          <td>
                            <select
                              className="cell-select"
                              value={row.unit}
                              onChange={(e) =>
                                handleInventoryCellChange(idx, 'unit', e.target.value)
                              }
                            >
                              {UNITS.map((u) => (
                                <option key={u} value={u}>
                                  {u}
                                </option>
                              ))}
                            </select>
                          </td>
                          <td>
                            <select
                              className="cell-select"
                              value={row.category}
                              onChange={(e) =>
                                handleInventoryCellChange(idx, 'category', e.target.value)
                              }
                            >
                              {CATEGORIES.map((c) => (
                                <option key={c} value={c}>
                                  {c}
                                </option>
                              ))}
                            </select>
                          </td>
                          <td>
                            <button
                              type="button"
                              className="btn btn-danger btn-icon"
                              onClick={() => handleDeleteInventoryRow(idx)}
                              title="Delete row"
                            >
                              🗑️
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="table-footer-actions">
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={handleAddInventoryRow}
                  >
                    ➕ Add Row
                  </button>
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={handleSaveInventoryTable}
                  >
                    {t('btn_save_inv')}
                  </button>
                </div>

                <details className="expander-box">
                  <summary>
                    ➕{' '}
                    {lang === 'en'
                      ? 'Quick Add New Inventory Item'
                      : 'নতুন পণ্য যোগ করুন (Quick Add)'}
                  </summary>
                  <form className="form-grid" onSubmit={handleQuickAddInventory}>
                    <div className="form-field">
                      <label>
                        Item Name (supports typos/Bengali like &apos;potto&apos;, &apos;alu&apos;, &apos;cheese&apos;)
                      </label>
                      <input
                        type="text"
                        placeholder="e.g. Potato / আলু / potto"
                        value={newInv.item_name}
                        onChange={(e) =>
                          setNewInv({ ...newInv, item_name: e.target.value })
                        }
                        required
                      />
                    </div>
                    <div className="form-field">
                      <label>Quantity</label>
                      <input
                        type="number"
                        step="1"
                        min="0"
                        value={newInv.quantity}
                        onChange={(e) =>
                          setNewInv({ ...newInv, quantity: e.target.value })
                        }
                        required
                      />
                    </div>
                    <div className="form-field">
                      <label>Unit</label>
                      <select
                        value={newInv.unit}
                        onChange={(e) => setNewInv({ ...newInv, unit: e.target.value })}
                      >
                        {UNITS.map((u) => (
                          <option key={u} value={u}>
                            {u}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="form-field">
                      <label>Category</label>
                      <select
                        value={newInv.category}
                        onChange={(e) =>
                          setNewInv({ ...newInv, category: e.target.value })
                        }
                      >
                        {CATEGORIES.map((c) => (
                          <option key={c} value={c}>
                            {c}
                          </option>
                        ))}
                      </select>
                    </div>
                    <button type="submit" className="btn btn-primary">
                      {lang === 'en'
                        ? 'Add Item to Inventory'
                        : 'পণ্য ইনভেন্টরিতে যোগ করুন'}
                    </button>
                  </form>
                </details>
              </>
            )}

            {/* --- Subtab 2: Suppliers --- */}
            {dataSubTab === 'suppliers' && (
              <>
                <h4 style={{ fontSize: '1rem', fontWeight: 700 }}>
                  {lang === 'en' ? 'Supplier Directory' : 'সরবরাহকারী তালিকা'}
                </h4>

                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Supplier Company</th>
                        <th>Contact Person</th>
                        <th>Phone</th>
                        <th>Email</th>
                        <th>Categories Supplied</th>
                        <th style={{ width: '60px' }}></th>
                      </tr>
                    </thead>
                    <tbody>
                      {suppliers.map((sup, idx) => (
                        <tr key={sup.id || idx}>
                          <td>
                            <input
                              type="text"
                              className="cell-input"
                              value={sup.name}
                              placeholder="Company name..."
                              onChange={(e) =>
                                handleSupplierCellChange(idx, 'name', e.target.value)
                              }
                            />
                          </td>
                          <td>
                            <input
                              type="text"
                              className="cell-input"
                              value={sup.contact_person || ''}
                              onChange={(e) =>
                                handleSupplierCellChange(
                                  idx,
                                  'contact_person',
                                  e.target.value
                                )
                              }
                            />
                          </td>
                          <td>
                            <input
                              type="text"
                              className="cell-input"
                              value={sup.phone || ''}
                              onChange={(e) =>
                                handleSupplierCellChange(idx, 'phone', e.target.value)
                              }
                            />
                          </td>
                          <td>
                            <input
                              type="text"
                              className="cell-input"
                              value={sup.email || ''}
                              onChange={(e) =>
                                handleSupplierCellChange(idx, 'email', e.target.value)
                              }
                            />
                          </td>
                          <td>
                            <input
                              type="text"
                              className="cell-input"
                              value={sup.supplied_categories || ''}
                              onChange={(e) =>
                                handleSupplierCellChange(
                                  idx,
                                  'supplied_categories',
                                  e.target.value
                                )
                              }
                            />
                          </td>
                          <td>
                            <button
                              type="button"
                              className="btn btn-danger btn-icon"
                              onClick={() => handleDeleteSupplierRow(idx)}
                              title="Delete row"
                            >
                              🗑️
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="table-footer-actions">
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={handleAddSupplierRow}
                  >
                    ➕ Add Row
                  </button>
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={handleSaveSuppliersTable}
                  >
                    {t('btn_save_sup')}
                  </button>
                </div>

                <details className="expander-box">
                  <summary>
                    ➕{' '}
                    {lang === 'en'
                      ? 'Quick Add New Supplier'
                      : 'নতুন সরবরাহকারী যোগ করুন'}
                  </summary>
                  <form className="form-grid" onSubmit={handleQuickAddSupplier}>
                    <div className="form-field">
                      <label>Supplier Company Name</label>
                      <input
                        type="text"
                        placeholder="e.g. Royal Spice Traders"
                        value={newSup.name}
                        onChange={(e) => setNewSup({ ...newSup, name: e.target.value })}
                        required
                      />
                    </div>
                    <div className="form-field">
                      <label>Contact Person</label>
                      <input
                        type="text"
                        placeholder="e.g. Deepak Kumar"
                        value={newSup.contact_person}
                        onChange={(e) =>
                          setNewSup({ ...newSup, contact_person: e.target.value })
                        }
                      />
                    </div>
                    <div className="form-field">
                      <label>Phone</label>
                      <input
                        type="text"
                        placeholder="+91 99999 00000"
                        value={newSup.phone}
                        onChange={(e) => setNewSup({ ...newSup, phone: e.target.value })}
                      />
                    </div>
                    <div className="form-field">
                      <label>Email</label>
                      <input
                        type="email"
                        placeholder="contact@royalspice.com"
                        value={newSup.email}
                        onChange={(e) => setNewSup({ ...newSup, email: e.target.value })}
                      />
                    </div>
                    <div className="form-field">
                      <label>Categories Supplied</label>
                      <input
                        type="text"
                        placeholder="Spices, Seasoning, Herbs"
                        value={newSup.supplied_categories}
                        onChange={(e) =>
                          setNewSup({
                            ...newSup,
                            supplied_categories: e.target.value,
                          })
                        }
                      />
                    </div>
                    <button type="submit" className="btn btn-primary">
                      {lang === 'en' ? 'Add Supplier' : 'সরবরাহকারী যোগ করুন'}
                    </button>
                  </form>
                </details>
              </>
            )}

            {/* --- Subtab 3: Orders --- */}
            {dataSubTab === 'orders' && (
              <>
                <h4 style={{ fontSize: '1rem', fontWeight: 700 }}>
                  {lang === 'en' ? 'Purchase Orders' : 'ক্রয় ও সরবরাহ অর্ডারসমূহ'}
                </h4>

                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Order #</th>
                        <th>Item</th>
                        <th>Quantity</th>
                        <th>Unit</th>
                        <th>Supplier Name</th>
                        <th>Status</th>
                        <th style={{ width: '60px' }}></th>
                      </tr>
                    </thead>
                    <tbody>
                      {orders.map((ord, idx) => (
                        <tr key={ord.id || idx}>
                          <td>
                            <input
                              type="text"
                              className="cell-input"
                              value={ord.order_number}
                              onChange={(e) =>
                                handleOrderCellChange(idx, 'order_number', e.target.value)
                              }
                            />
                          </td>
                          <td>
                            <input
                              type="text"
                              className="cell-input"
                              value={ord.item_name}
                              onChange={(e) =>
                                handleOrderCellChange(idx, 'item_name', e.target.value)
                              }
                            />
                          </td>
                          <td style={{ maxWidth: '120px' }}>
                            <input
                              type="number"
                              step="1"
                              min="0"
                              className="cell-input"
                              value={ord.quantity}
                              onChange={(e) =>
                                handleOrderCellChange(idx, 'quantity', e.target.value)
                              }
                            />
                          </td>
                          <td>
                            <select
                              className="cell-select"
                              value={ord.unit}
                              onChange={(e) =>
                                handleOrderCellChange(idx, 'unit', e.target.value)
                              }
                            >
                              {UNITS.map((u) => (
                                <option key={u} value={u}>
                                  {u}
                                </option>
                              ))}
                            </select>
                          </td>
                          <td>
                            <input
                              type="text"
                              className="cell-input"
                              value={ord.supplier_name}
                              onChange={(e) =>
                                handleOrderCellChange(idx, 'supplier_name', e.target.value)
                              }
                            />
                          </td>
                          <td>
                            <select
                              className="cell-select"
                              value={ord.status}
                              onChange={(e) =>
                                handleOrderCellChange(idx, 'status', e.target.value)
                              }
                            >
                              {ORDER_STATUSES.map((st) => (
                                <option key={st} value={st}>
                                  {st}
                                </option>
                              ))}
                            </select>
                          </td>
                          <td>
                            <button
                              type="button"
                              className="btn btn-danger btn-icon"
                              onClick={() => handleDeleteOrderRow(idx)}
                              title="Delete row"
                            >
                              🗑️
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="table-footer-actions">
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={handleAddOrderRow}
                  >
                    ➕ Add Row
                  </button>
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={handleSaveOrdersTable}
                  >
                    {t('btn_save_ord')}
                  </button>
                </div>

                <details className="expander-box">
                  <summary>
                    ➕{' '}
                    {lang === 'en'
                      ? 'Create New Order Record'
                      : 'নতুন অর্ডার রেকর্ড তৈরি করুন'}
                  </summary>
                  <form className="form-grid" onSubmit={handleQuickAddOrder}>
                    <div className="form-field">
                      <label>Order Number</label>
                      <input
                        type="text"
                        placeholder="e.g. ORD-1004"
                        value={newOrd.order_number}
                        onChange={(e) =>
                          setNewOrd({ ...newOrd, order_number: e.target.value })
                        }
                        required
                      />
                    </div>
                    <div className="form-field">
                      <label>Item Name</label>
                      <input
                        type="text"
                        placeholder="e.g. Cooking Oil"
                        value={newOrd.item_name}
                        onChange={(e) =>
                          setNewOrd({ ...newOrd, item_name: e.target.value })
                        }
                        required
                      />
                    </div>
                    <div className="form-field">
                      <label>Quantity</label>
                      <input
                        type="number"
                        step="1"
                        min="1"
                        value={newOrd.quantity}
                        onChange={(e) =>
                          setNewOrd({ ...newOrd, quantity: e.target.value })
                        }
                        required
                      />
                    </div>
                    <div className="form-field">
                      <label>Unit</label>
                      <select
                        value={newOrd.unit}
                        onChange={(e) => setNewOrd({ ...newOrd, unit: e.target.value })}
                      >
                        {UNITS.map((u) => (
                          <option key={u} value={u}>
                            {u}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="form-field">
                      <label>Supplier Name</label>
                      <input
                        type="text"
                        placeholder="e.g. Golden Grain Traders"
                        value={newOrd.supplier_name}
                        onChange={(e) =>
                          setNewOrd({ ...newOrd, supplier_name: e.target.value })
                        }
                        required
                      />
                    </div>
                    <div className="form-field">
                      <label>Status</label>
                      <select
                        value={newOrd.status}
                        onChange={(e) => setNewOrd({ ...newOrd, status: e.target.value })}
                      >
                        {ORDER_STATUSES.map((st) => (
                          <option key={st} value={st}>
                            {st}
                          </option>
                        ))}
                      </select>
                    </div>
                    <button type="submit" className="btn btn-primary">
                      {lang === 'en' ? 'Record Order' : 'অর্ডার রেকর্ড সংরক্ষণ করুন'}
                    </button>
                  </form>
                </details>
              </>
            )}
          </section>
        )}

        {/* ================= TAB 3: ACTION APPROVALS ================= */}
        {activeTab === 'approvals' && (
          <section className="panel-card">
            <div className="panel-header">
              <div>
                <h3>{t('tab_approvals')}</h3>
                <p>
                  {lang === 'en'
                    ? 'Safeguard operational writes: Review, approve, or reject draft purchase orders proposed by HutMate AI or kitchen staff.'
                    : 'অপারেশনাল অনুমোদন: এআই বা কর্মচারীদের প্রস্তাবিত ড্রাফট অর্ডার পর্যালোচনা করুন, অনুমোদন দিন অথবা বাতিল করুন।'}
                </p>
              </div>

              <div className="subtabs-nav">
                <button
                  className={`subtab-btn ${approvalSubTab === 'pending' ? 'active' : ''}`}
                  onClick={() => setApprovalSubTab('pending')}
                >
                  {t('subtab_pending')} ({pendingRequests.length})
                </button>
                <button
                  className={`subtab-btn ${approvalSubTab === 'history' ? 'active' : ''}`}
                  onClick={() => setApprovalSubTab('history')}
                >
                  {t('subtab_history')} ({allRequests.length})
                </button>
              </div>
            </div>

            {/* --- Approval Subtab 1: Pending Queue --- */}
            {approvalSubTab === 'pending' && (
              <>
                {pendingRequests.length === 0 ? (
                  <div className="empty-state">
                    {lang === 'en'
                      ? '🎉 No pending purchase requests. All caught up!'
                      : '🎉 কোনো অপেক্ষমাণ ক্রয় প্রস্তাব নেই। সব আপডেট রয়েছে!'}
                  </div>
                ) : (
                  <div className="approval-list">
                    {pendingRequests.map((req) => {
                      const localizedItem =
                        lang !== 'en'
                          ? `${req.item_name} (${lang === 'hi' ? req.display_hi || req.display_bn : req.display_bn})`
                          : req.item_name
                      return (
                        <div key={req.id} className="approval-card">
                          <div className="approval-info">
                            <h4>
                              Request #{req.id} — Order {localizedItem}
                            </h4>
                            <div className="approval-meta">
                              <span>
                                <strong>Quantity:</strong>{' '}
                                <code>
                                  {req.quantity} {req.unit}
                                </code>
                              </span>
                              <span>
                                <strong>Supplier:</strong>{' '}
                                <code>{req.supplier_name}</code>
                              </span>
                            </div>
                            <div className="approval-timestamp">
                              Requested on: {req.created_at || 'Just now'}
                            </div>
                          </div>

                          <div className="approval-actions">
                            <button
                              type="button"
                              className="btn btn-success"
                              onClick={() => handleResolveRequest(req.id, 'APPROVED')}
                            >
                              {t('btn_approve')}
                            </button>
                            <button
                              type="button"
                              className="btn btn-danger"
                              onClick={() => handleResolveRequest(req.id, 'REJECTED')}
                            >
                              {t('btn_reject')}
                            </button>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )}

                <details className="expander-box">
                  <summary>
                    ➕{' '}
                    {lang === 'en'
                      ? 'Manually Draft a Purchase Request'
                      : 'ম্যানুয়ালি পারচেস রিকোয়েস্ট তৈরি করুন'}
                  </summary>
                  <form className="form-grid" onSubmit={handleManualDraftSubmit}>
                    <div className="form-field">
                      <label>Item Name</label>
                      <input
                        type="text"
                        placeholder="e.g. Basmati Rice / আলু / Aloo"
                        value={manualDraft.item_name}
                        onChange={(e) =>
                          setManualDraft({ ...manualDraft, item_name: e.target.value })
                        }
                        required
                      />
                    </div>
                    <div className="form-field">
                      <label>Quantity</label>
                      <input
                        type="number"
                        step="1"
                        min="1"
                        value={manualDraft.quantity}
                        onChange={(e) =>
                          setManualDraft({ ...manualDraft, quantity: e.target.value })
                        }
                        required
                      />
                    </div>
                    <div className="form-field">
                      <label>Unit</label>
                      <select
                        value={manualDraft.unit}
                        onChange={(e) =>
                          setManualDraft({ ...manualDraft, unit: e.target.value })
                        }
                      >
                        {UNITS.map((u) => (
                          <option key={u} value={u}>
                            {u}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="form-field">
                      <label>Supplier Name</label>
                      <input
                        type="text"
                        placeholder="e.g. Golden Grain Traders"
                        value={manualDraft.supplier_name}
                        onChange={(e) =>
                          setManualDraft({
                            ...manualDraft,
                            supplier_name: e.target.value,
                          })
                        }
                        required
                      />
                    </div>
                    <button type="submit" className="btn btn-primary">
                      {lang === 'en'
                        ? 'Submit Draft for Approval'
                        : 'অনুমোদনের জন্য পাঠান'}
                    </button>
                  </form>
                </details>
              </>
            )}

            {/* --- Approval Subtab 2: History & Audit Trail --- */}
            {approvalSubTab === 'history' && (
              <>
                {allRequests.length === 0 ? (
                  <div className="empty-state" style={{ background: '#eff6ff', color: '#1d4ed8', borderColor: '#bfdbfe' }}>
                    {lang === 'en'
                      ? 'No purchase requests recorded yet.'
                      : 'এখনো পর্যন্ত কোনো ক্রয়ের রেকর্ড নেই।'}
                  </div>
                ) : (
                  <div className="table-container">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Req #</th>
                          <th>Item / পণ্য</th>
                          <th>Quantity / পরিমাণ</th>
                          <th>Unit / একক</th>
                          <th>Supplier / সরবরাহকারী</th>
                          <th>Status</th>
                          <th>Created At</th>
                          <th>Resolved At</th>
                        </tr>
                      </thead>
                      <tbody>
                        {allRequests.map((req) => (
                          <tr key={req.id}>
                            <td>
                              <strong>#{req.id}</strong>
                            </td>
                            <td>{req.item_name}</td>
                            <td>{Number(req.quantity).toFixed(2)}</td>
                            <td>{req.unit}</td>
                            <td>{req.supplier_name}</td>
                            <td>
                              <span className={`status-badge status-${req.status}`}>
                                {req.status}
                              </span>
                            </td>
                            <td>{req.created_at || '—'}</td>
                            <td>{req.resolved_at || '—'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </>
            )}
          </section>
        )}
      </main>
    </div>
  )
}

