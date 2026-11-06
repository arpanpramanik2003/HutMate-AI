import React from 'react'

export default function Toast({ toast, onClose }) {
  if (!toast) return null

  return (
    <div className={`toast-banner ${toast.type}`}>
      <span>{toast.message}</span>
      <button className="toast-close" onClick={onClose} aria-label="Close notification">
        ✕
      </button>
    </div>
  )
}

