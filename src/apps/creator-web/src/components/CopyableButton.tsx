'use client'

import React, { useState } from 'react'

interface CopyableButtonProps {
  textToCopy: string
  label?: string
  copiedLabel?: string
  className?: string
  style?: React.CSSProperties
}

export default function CopyableButton({
  textToCopy,
  label = 'Copy',
  copiedLabel = 'Copied! ✓',
  className = 'btn',
  style
}: CopyableButtonProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(textToCopy)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy text:', err)
    }
  }

  return (
    <button
      onClick={handleCopy}
      className={className}
      style={{
        ...style,
        background: copied ? '#10b981' : style?.background,
        transition: 'all 0.2s ease'
      }}
    >
      {copied ? copiedLabel : label}
    </button>
  )
}
