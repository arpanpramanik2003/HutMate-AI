import React, { useState, useEffect, useRef } from 'react'
import Header from './components/common/Header'
import Sidebar from './components/common/Sidebar'
import Toast from './components/common/Toast'
import ChatTab from './components/chat/ChatTab'
import DataTab from './components/data/DataTab'
import ApprovalsTab from './components/approvals/ApprovalsTab'
import { FALLBACK_TRANSLATIONS } from './constants/config'

export default function App() {
  const [lang, setLang] = useState('en')
  const [translations, setTranslations] = useState(FALLBACK_TRANSLATIONS)
  const [activeTab, setActiveTab] = useState('chat')
  const [dataSubTab, setDataSubTab] = useState('inventory')
  const [approvalSubTab, setApprovalSubTab] = useState('pending')

  // RBAC active role and available roles
  const [userRole, setUserRole] = useState('OWNER')
  const [roles, setRoles] = useState([])

  // Mobile sidebar drawer state
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)

  // Live state from backend
  const [indexedChunks, setIndexedChunks] = useState(0)
  const [inventory, setInventory] = useState([])
  const [lowStockAlerts, setLowStockAlerts] = useState([])
  const [recipes, setRecipes] = useState([])
  const [kitchenSales, setKitchenSales] = useState([])
  const [suppliers, setSuppliers] = useState([])
  const [orders, setOrders] = useState([])
  const [pendingRequests, setPendingRequests] = useState([])
  const [allRequests, setAllRequests] = useState([])

  // Toast notifications
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

  // Unified API Fetch helper injecting X-User-Role and handling errors
  const apiFetch = async (url, options = {}) => {
    const headers = {
      'X-User-Role': userRole,
      ...(options.headers || {}),
    }
    if (
      !(options.body instanceof FormData) &&
      !headers['Content-Type'] &&
      options.method &&
      options.method !== 'GET'
    ) {
      headers['Content-Type'] = 'application/json'
    }
    const res = await fetch(url, { ...options, headers })
    const data = await res.json().catch(() => ({}))
    if (!res.ok) {
      throw new Error(data.detail || `Request failed with status ${res.status}`)
    }
    return data
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

  // Sidebar loading states
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
    min_par_level: 5.0,
    cost_per_unit: 0.0,
    expiry_date: '',
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
    if (Array.isArray(state.roles)) setRoles(state.roles)
    if (typeof state.indexed_chunks === 'number') setIndexedChunks(state.indexed_chunks)
    if (Array.isArray(state.inventory)) setInventory(state.inventory)
    if (Array.isArray(state.low_stock_alerts)) setLowStockAlerts(state.low_stock_alerts)
    if (Array.isArray(state.recipes)) setRecipes(state.recipes)
    if (Array.isArray(state.kitchen_sales)) setKitchenSales(state.kitchen_sales)
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
      const data = await apiFetch('/api/system/reseed', { method: 'POST' })
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
      const data = await apiFetch('/api/rag/load-samples', { method: 'POST' })
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
      const data = await apiFetch('/api/rag/upload', {
        method: 'POST',
        body: formData,
      })
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

  // Operations Chat submission
  const sendChatMessage = async (promptText) => {
    const trimmed = (promptText ?? chatInput).trim()
    if (!trimmed || isChatLoading) return

    const updatedHistory = [...messages, { role: 'user', content: trimmed }]
    setMessages(updatedHistory)
    setChatInput('')
    setIsChatLoading(true)

    try {
      const data = await apiFetch('/api/chat', {
        method: 'POST',
        body: JSON.stringify({
          message: trimmed,
          history: messages.map((m) => ({ role: m.role, content: m.content })),
          language: lang,
        }),
      })
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

  // Kitchen Production / Dish Sales Handler
  const handleRecordDishSales = async (dishName, portions) => {
    try {
      const data = await apiFetch('/api/kitchen/sales', {
        method: 'POST',
        body: JSON.stringify({ dish_name: dishName, portions: parseFloat(portions) }),
      })
      if (data.state) applyBackendState(data.state)
      if (data.result?.status === 'success') {
        showToast(`✅ Deducted ingredients for ${portions}x ${dishName}!`, 'success')
        if (data.result?.low_stock_warnings?.length > 0) {
          setTimeout(() => {
            showToast(`⚠️ Low stock alert: ${data.result.low_stock_warnings[0]}`, 'warning')
          }, 2000)
        }
      } else {
        showToast(`⚠️ ${data.result?.message || 'Stock deduction failed'}`, 'error')
      }
    } catch (err) {
      showToast(`Kitchen deduction error: ${err.message}`, 'error')
    }
  }

  // Inventory Handlers
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
        min_par_level: 5.0,
        cost_per_unit: 0.0,
        expiry_date: '',
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
          min_par_level: parseFloat(r.min_par_level) || 5.0,
          cost_per_unit: parseFloat(r.cost_per_unit) || 0.0,
          expiry_date: r.expiry_date || '',
        }))
      const data = await apiFetch('/api/inventory/sync', {
        method: 'PUT',
        body: JSON.stringify({ items: validItems }),
      })
      if (data.inventory) setInventory(data.inventory)
      if (data.low_stock_alerts) setLowStockAlerts(data.low_stock_alerts)
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
      const data = await apiFetch('/api/inventory', {
        method: 'POST',
        body: JSON.stringify({
          item_name: newInv.item_name,
          quantity: parseFloat(newInv.quantity) || 0,
          unit: newInv.unit,
          category: newInv.category,
          min_par_level: parseFloat(newInv.min_par_level) || 5.0,
          cost_per_unit: parseFloat(newInv.cost_per_unit) || 0.0,
          expiry_date: newInv.expiry_date || '',
        }),
      })
      if (data.inventory) setInventory(data.inventory)
      if (data.low_stock_alerts) setLowStockAlerts(data.low_stock_alerts)
      setNewInv({
        item_name: '',
        quantity: 10.0,
        unit: 'kg',
        category: 'Produce',
        min_par_level: 5.0,
        cost_per_unit: 0.0,
        expiry_date: '',
      })
      showToast(
        `Added: ${data.result?.item_name || newInv.item_name} (${data.result?.display_bn || ''})!`,
        'success'
      )
    } catch (err) {
      showToast(`Error adding item: ${err.message}`, 'error')
    }
  }

  // Suppliers Handlers
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
      const data = await apiFetch('/api/suppliers/sync', {
        method: 'PUT',
        body: JSON.stringify({ items: validSuppliers }),
      })
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
      const data = await apiFetch('/api/suppliers', {
        method: 'POST',
        body: JSON.stringify(newSup),
      })
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

  // Orders Handlers
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
      const data = await apiFetch('/api/orders/sync', {
        method: 'PUT',
        body: JSON.stringify({ items: validOrders }),
      })
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
      const data = await apiFetch('/api/orders', {
        method: 'POST',
        body: JSON.stringify({
          ...newOrd,
          quantity: parseFloat(newOrd.quantity) || 1.0,
        }),
      })
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

  // Action Approvals Handlers
  const handleResolveRequest = async (reqId, decision) => {
    try {
      const data = await apiFetch(`/api/approvals/${reqId}/resolve`, {
        method: 'POST',
        body: JSON.stringify({ decision }),
      })
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
      const data = await apiFetch('/api/approvals', {
        method: 'POST',
        body: JSON.stringify({
          ...manualDraft,
          quantity: parseFloat(manualDraft.quantity) || 1.0,
        }),
      })
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

  return (
    <div className="app-shell">
      {/* Mobile Drawer Backdrop */}
      <div
        className={`sidebar-backdrop ${isSidebarOpen ? 'active' : ''}`}
        onClick={() => setIsSidebarOpen(false)}
        aria-hidden="true"
      />

      {/* Sidebar Navigation & Controls */}
      <Sidebar
        lang={lang}
        onLanguageChange={handleLanguageChange}
        isReseeding={isReseeding}
        onReseed={handleReseed}
        isIndexingSamples={isIndexingSamples}
        onLoadSamples={handleLoadSamples}
        fileInputRef={fileInputRef}
        onFileSelect={handleFileSelect}
        selectedFiles={selectedFiles}
        onRemoveSelectedFile={handleRemoveSelectedFile}
        isUploadingDocs={isUploadingDocs}
        onIndexUploadedDocs={handleIndexUploadedDocs}
        indexedChunks={indexedChunks}
        lowStockAlerts={lowStockAlerts}
        t={t}
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
      />

      {/* Main Workspace Area */}
      <main className="main-workspace">
        <Header
          t={t}
          userRole={userRole}
          onRoleChange={setUserRole}
          roles={roles}
          onToggleSidebar={() => setIsSidebarOpen((prev) => !prev)}
        />

        <Toast toast={toast} onClose={() => setToast(null)} />

        {/* Primary Tabs Navigation */}
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
            {lowStockAlerts.length > 0 && (
              <span className="tab-badge urgent" title="Items below par level">
                ⚠️ {lowStockAlerts.length}
              </span>
            )}
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

        {/* Tab 1: Operations Chat */}
        {activeTab === 'chat' && (
          <ChatTab
            messages={messages}
            isChatLoading={isChatLoading}
            chatInput={chatInput}
            onChatInputChange={setChatInput}
            onSendMessage={sendChatMessage}
            onClearChat={handleClearChat}
            chatEndRef={chatEndRef}
            lang={lang}
            t={t}
          />
        )}

        {/* Tab 2: Live Restaurant Data (Inventory, Recipes/BOM, Suppliers, Orders) */}
        {activeTab === 'data' && (
          <DataTab
            dataSubTab={dataSubTab}
            onSubTabChange={setDataSubTab}
            inventory={inventory}
            onInventoryCellChange={handleInventoryCellChange}
            onAddInventoryRow={handleAddInventoryRow}
            onDeleteInventoryRow={handleDeleteInventoryRow}
            onSaveInventoryTable={handleSaveInventoryTable}
            newInv={newInv}
            onNewInvChange={setNewInv}
            onQuickAddInventory={handleQuickAddInventory}
            recipes={recipes}
            kitchenSales={kitchenSales}
            onRecordDishSales={handleRecordDishSales}
            suppliers={suppliers}
            onSupplierCellChange={handleSupplierCellChange}
            onAddSupplierRow={handleAddSupplierRow}
            onDeleteSupplierRow={handleDeleteSupplierRow}
            onSaveSuppliersTable={handleSaveSuppliersTable}
            newSup={newSup}
            onNewSupChange={setNewSup}
            onQuickAddSupplier={handleQuickAddSupplier}
            orders={orders}
            onOrderCellChange={handleOrderCellChange}
            onAddOrderRow={handleAddOrderRow}
            onDeleteOrderRow={handleDeleteOrderRow}
            onSaveOrdersTable={handleSaveOrdersTable}
            newOrd={newOrd}
            onNewOrdChange={setNewOrd}
            onQuickAddOrder={handleQuickAddOrder}
            lang={lang}
            t={t}
          />
        )}

        {/* Tab 3: Action Approvals */}
        {activeTab === 'approvals' && (
          <ApprovalsTab
            approvalSubTab={approvalSubTab}
            onSubTabChange={setApprovalSubTab}
            pendingRequests={pendingRequests}
            allRequests={allRequests}
            onResolveRequest={handleResolveRequest}
            manualDraft={manualDraft}
            onManualDraftChange={setManualDraft}
            onManualDraftSubmit={handleManualDraftSubmit}
            lang={lang}
            t={t}
            userRole={userRole}
          />
        )}
      </main>
    </div>
  )
}
