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
  t,
}) {
  return (
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
          onChange={(e) => onLanguageChange(e.target.value)}
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
                  onClick={() => onRemoveSelectedFile(i)}
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
            onClick={onIndexUploadedDocs}
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
  )
}

