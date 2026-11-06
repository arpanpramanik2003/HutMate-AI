import React from 'react'
import ChatMessage from './ChatMessage'
import PromptChips from './PromptChips'
import { DEMO_PROMPTS } from '../../constants/config'

export default function ChatTab({
  messages,
  isChatLoading,
  chatInput,
  onChatInputChange,
  onSendMessage,
  onClearChat,
  chatEndRef,
  lang,
  t,
}) {
  const thinkingText =
    lang === 'en'
      ? 'HutMate AI is thinking and consulting operational tools...'
      : lang === 'bn'
        ? 'হাটমেট এআই তথ্য বিশ্লেষণ করছে...'
        : 'हटमेट एआई जानकारी का विश्लेषण कर रहा है...'

  return (
    <section className="chat-wrapper">
      <div className="chat-top-bar">
        <div>
          <h3 style={{ fontSize: '1.08rem', fontWeight: 700 }}>
            {t('chat_heading')}
          </h3>
          <p style={{ fontSize: '0.82rem', color: '#64748b' }}>
            {t('chat_caption')}
          </p>
        </div>
        <button className="btn btn-secondary" onClick={onClearChat}>
          {t('btn_clear_chat')}
        </button>
      </div>

      <div className="chat-feed">
        {messages.map((msg, idx) => (
          <ChatMessage key={idx} msg={msg} lang={lang} />
        ))}

        {isChatLoading && (
          <div className="chat-msg assistant">
            <div className="chat-avatar">🤖</div>
            <div className="chat-bubble">
              <div className="chat-text" style={{ color: '#64748b', fontStyle: 'italic' }}>
                ⏳ {thinkingText}
              </div>
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Quick Try Prompts */}
      <PromptChips
        prompts={DEMO_PROMPTS}
        onSelectPrompt={onSendMessage}
        disabled={isChatLoading}
      />

      {/* Chat Input Bar */}
      <form
        className="chat-input-bar"
        onSubmit={(e) => {
          e.preventDefault()
          onSendMessage()
        }}
      >
        <input
          type="text"
          className="chat-input"
          placeholder={t('chat_placeholder')}
          value={chatInput}
          onChange={(e) => onChatInputChange(e.target.value)}
          disabled={isChatLoading}
        />
        <button
          type="submit"
          className="btn btn-primary"
          disabled={isChatLoading || !chatInput.trim()}
        >
          {lang === 'en' ? 'Send ➤' : lang === 'bn' ? 'পাঠান ➤' : 'भेजें ➤'}
        </button>
      </form>
    </section>
  )
}

