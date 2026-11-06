import React from 'react'
import { UNITS } from '../../constants/config'

export default function PendingQueue({
  pendingRequests,
  onResolveRequest,
  manualDraft,
  onManualDraftChange,
  onManualDraftSubmit,
  lang,
  t,
}) {
  return (
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
                    <span>
                      <strong>Est. Financial Commitment:</strong>{' '}
                      <code style={{ color: '#047857', fontWeight: 700 }}>
                        {req.estimated_cost_formatted || (req.estimated_cost ? `₹${Number(req.estimated_cost).toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : 'Quote pending')}
                      </code>
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
                    onClick={() => onResolveRequest(req.id, 'APPROVED')}
                  >
                    {t('btn_approve')}
                  </button>
                  <button
                    type="button"
                    className="btn btn-danger"
                    onClick={() => onResolveRequest(req.id, 'REJECTED')}
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
        <form className="form-grid" onSubmit={onManualDraftSubmit}>
          <div className="form-field">
            <label>Item Name</label>
            <input
              type="text"
              placeholder="e.g. Basmati Rice / আলু / Aloo"
              value={manualDraft.item_name}
              onChange={(e) =>
                onManualDraftChange({ ...manualDraft, item_name: e.target.value })
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
                onManualDraftChange({ ...manualDraft, quantity: e.target.value })
              }
              required
            />
          </div>
          <div className="form-field">
            <label>Unit</label>
            <select
              value={manualDraft.unit}
              onChange={(e) =>
                onManualDraftChange({ ...manualDraft, unit: e.target.value })
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
                onManualDraftChange({
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
  )
}

