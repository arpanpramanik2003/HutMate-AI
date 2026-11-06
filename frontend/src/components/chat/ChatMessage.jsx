import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export default function ChatMessage({ msg, lang }) {
  return (
    <div className={`chat-msg ${msg.role}`}>
      <div className="chat-avatar">
        {msg.role === 'user' ? '🧑‍🍳' : '🤖'}
      </div>
      <div className="chat-bubble">
        <div className="chat-text">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {msg.content}
          </ReactMarkdown>
        </div>

        {msg.tools_used && msg.tools_used.length > 0 && (
          <details className="tools-details">
            <summary>
              🛠️{' '}
              {lang === 'en'
                ? `Operational Tools Invoked (${msg.tools_used.length})`
                : `ব্যবহৃত অপারেশনাল টুলস (${msg.tools_used.length})`}
            </summary>
            <pre>{JSON.stringify(msg.tools_used, null, 2)}</pre>
          </details>
        )}

        {msg.sources && msg.sources.length > 0 && (
          <div className="sources-row">
            <span>📚 Sources:</span>
            {Array.from(new Set(msg.sources)).map((src, sIdx) => (
              <span key={sIdx} className="source-pill">
                {src}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

