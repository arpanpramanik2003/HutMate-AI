import React from 'react'

export default function Sidebar({
  lang,
  onLanguageChange,
  isReseeding,
  onReseed,
  isIndexingSamples,
  onLoadSamples,
  fileInputRef,
  onFileSelect,
  selectedFiles,
  onRemoveSelectedFile,
  isUploadingDocs,
  onIndexUploadedDocs,
  indexedChunks,
  lowStockAlerts,
  t,
  isOpen = false,
  onClose,
}) {
  return (
    <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
      <div className="sidebar-brand">
        <div className="sidebar-brand-left">
          <div className="sidebar-brand-icon">🍽️</div>
          <div className="sidebar-brand-text">
            <h2>HutMate AI</h2>
            <span>Operations Copilot</span>
          </div>
        </div>

        <button
          type="button"
          className="mobile-sidebar-close"
          onClick={onClose}
          aria-label="Close Sidebar Menu"
          title="Close Menu"
        >
          ✕
        </button>
      </div>

      {/* Language Selector */}
      <div className="sidebar-section">
        <div className="sidebar-section-title">
          🌐 {lang === 'bn' ? 'Language / ভাষা' : 'Language / भाषा / ভাষা'}
        </div>
        <select
          className="sidebar-select"
          value={lang}
          onChange={(e) => onLanguageChange(e.target.value)}
          aria-label="System Language"
        >
          <option value="en">🇬🇧 English</option>
          <option value="bn">🇧🇩 বাংলা (Bengali)</option>
          <option value="hi">🇮🇳 हिंदी (Hindi)</option>
        </select>
      </div>

      {/* Low Stock Alerts Banner with Pulse Dot */}
      {lowStockAlerts && lowStockAlerts.length > 0 && (
        <div className="metric-card urgent-stock-card">
          <div className="urgent-card-header">
            <span className="pulse-dot"></span>
            <span className="metric-label alert-label">Par Level Alerts</span>
          </div>
          <span className="metric-value alert-value">
            {lowStockAlerts.length} item{lowStockAlerts.length > 1 ? 's' : ''} low
          </span>
          <div className="urgent-card-preview">
            {lowStockAlerts.map((a) => a.item_name).slice(0, 3).join(', ')}
            {lowStockAlerts.length > 3 ? '...' : ''}
          </div>
        </div>
      )}

      {/* System Operations */}
      <div className="sidebar-section">
        <div className="sidebar-section-title">{t('sidebar_sys_ops')}</div>
        <button
          className="sidebar-btn"
          onClick={onReseed}
          disabled={isReseeding}
        >
          {isReseeding ? '⏳ Resetting...' : t('btn_reseed')}
        </button>
        <button
          className="sidebar-btn"
          onClick={onLoadSamples}
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
            onChange={onFileSelect}
          />
          <div className="upload-icon">📂</div>
          <div className="upload-title">Select PDF, DOCX, TXT</div>
          <div className="upload-subtitle">Restaurant SOPs, Menus & Policies</div>
        </label>

        {selectedFiles.length > 0 && (
          <div className="file-list">
            {selectedFiles.map((file, i) => (
              <div key={`${file.name}-${i}`} className="file-pill">
                <span className="file-pill-name">📄 {file.name}</span>
                <button
                  type="button"
                  onClick={() => onRemoveSelectedFile(i)}
                  title="Remove file"
                  aria-label={`Remove ${file.name}`}
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
            onClick={onIndexUploadedDocs}
            disabled={isUploadingDocs}
          >
            {isUploadingDocs
              ? '⏳ Generating FastEmbed embeddings...'
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
  )
}
