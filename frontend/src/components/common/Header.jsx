import React from 'react'

export default function Header({ t, userRole, onRoleChange, roles = [] }) {
  return (
    <header className="top-header">
      <div>
        <h1>{t('app_title')}</h1>
        <p>{t('app_caption')}</p>
      </div>

      <div className="role-switcher-container">
        <label htmlFor="role-select" className="role-label">Active Role:</label>
        <select
          id="role-select"
          className="role-select"
          value={userRole}
          onChange={(e) => onRoleChange(e.target.value)}
        >
          {roles.length > 0 ? (
            roles.map((r) => (
              <option key={r.id} value={r.id}>
                {r.label}
              </option>
            ))
          ) : (
            <>
              <option value="OWNER">👑 Owner (Admin)</option>
              <option value="HEAD_CHEF">🧑‍🍳 Head Chef</option>
              <option value="LINE_COOK">🥘 Line Cook</option>
            </>
          )}
        </select>
      </div>
    </header>
  )
}
