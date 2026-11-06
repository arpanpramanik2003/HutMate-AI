import React from 'react'

export default function Header({ t }) {
  return (
    <header className="top-header">
      <div>
        <h1>{t('app_title')}</h1>
        <p>{t('app_caption')}</p>
      </div>
    </header>
  )
}

