import React from 'react'

export default function PromptChips({ prompts, onSelectPrompt, disabled }) {
  return (
    <div className="prompt-chips">
      {prompts.map((sample, idx) => (
        <button
          key={idx}
          type="button"
          className="prompt-chip"
          onClick={() => onSelectPrompt(sample)}
          disabled={disabled}
        >
          {sample}
        </button>
      ))}
    </div>
  )
}

