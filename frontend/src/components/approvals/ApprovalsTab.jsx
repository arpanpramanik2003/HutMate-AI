import React from 'react'
import PendingQueue from './PendingQueue'
import AuditHistory from './AuditHistory'

export default function ApprovalsTab({
  approvalSubTab,
  onSubTabChange,
  pendingRequests,
  allRequests,
  onResolveRequest,
  manualDraft,
  onManualDraftChange,
  onManualDraftSubmit,
  lang,
  t,
  userRole = 'OWNER',
}) {
  return (
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
            onClick={() => onSubTabChange('pending')}
          >
            {t('subtab_pending')} ({pendingRequests.length})
          </button>
          <button
            className={`subtab-btn ${approvalSubTab === 'history' ? 'active' : ''}`}
            onClick={() => onSubTabChange('history')}
          >
            {t('subtab_history')} ({allRequests.length})
          </button>
        </div>
      </div>

      {approvalSubTab === 'pending' && (
        <PendingQueue
          pendingRequests={pendingRequests}
          onResolveRequest={onResolveRequest}
          manualDraft={manualDraft}
          onManualDraftChange={onManualDraftChange}
          onManualDraftSubmit={onManualDraftSubmit}
          lang={lang}
          t={t}
          userRole={userRole}
        />
      )}

      {approvalSubTab === 'history' && (
        <AuditHistory allRequests={allRequests} lang={lang} />
      )}
    </section>
  )
}

