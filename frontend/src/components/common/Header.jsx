import React from 'react'

export default function Header({
  t,
  userRole,
  onRoleChange,
  roles = [],
  onToggleSidebar,
}) {
  return (
    <header className="top-header">
      <div className="header-left">
        <button
          type="button"
          className="mobile-sidebar-toggle"
          onClick={onToggleSidebar}
          aria-label="Toggle Navigation Menu"
          title="Open System Controls & Settings"
        >
          <span className="toggle-icon">☰</span>
          <span className="toggle-text">Menu</span>
        </button>

        <div className="header-branding">
          <div className="header-title-row">
            <h1>{t('app_title')}</h1>
            <span className="production-badge">PROD 2.0</span>
          </div>
          <p>{t('app_caption')}</p>
        </div>
      </div>

      <div className="role-switcher-container">
        <span className="role-icon">👤</span>
        <div className="role-control-group">
          <label htmlFor="role-select" className="role-label">Active Role</label>
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
      </div>
    </header>
  )
}
