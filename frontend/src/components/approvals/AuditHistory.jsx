import React from 'react'

export default function AuditHistory({ allRequests, lang }) {
  if (allRequests.length === 0) {
    return (
      <div
        className="empty-state"
        style={{ background: '#eff6ff', color: '#1d4ed8', borderColor: '#bfdbfe' }}
      >
        {lang === 'en'
          ? 'No purchase requests recorded yet.'
          : 'এখনো পর্যন্ত কোনো ক্রয়ের রেকর্ড নেই।'}
      </div>
    )
  }

  return (
    <div className="table-container">
      <table className="data-table">
        <thead>
          <tr>
            <th>Req #</th>
            <th>Item / পণ্য</th>
            <th>Quantity / পরিমাণ</th>
            <th>Unit / একক</th>
            <th>Supplier / সরবরাহকারী</th>
            <th>Est. Cost (₹)</th>
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
              <td style={{ color: '#047857', fontWeight: 600 }}>
                {req.estimated_cost ? `₹${Number(req.estimated_cost).toFixed(2)}` : '—'}
              </td>
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
  )
}

