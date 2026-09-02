'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

export default function SyncButton() {
  const [syncing, setSyncing] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const router = useRouter()

  const handleSync = async () => {
    setSyncing(true)
    setMessage(null)
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const res = await fetch(`${apiBase}/webhooks/shopify/sync`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
      const data = await res.json()
      if (res.ok) {
        setMessage(`Synced: ${data.new_orders || 0} new orders, ${data.refunds_processed || 0} refunds`)
        router.refresh()
      } else {
        setMessage(`Sync failed: ${data.detail || 'Error'}`)
      }
    } catch (e: any) {
      setMessage(`Network error: ${e.message}`)
    } finally {
      setSyncing(false)
    }
  }

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
      {message && (
        <span style={{ fontSize: '0.85rem', color: message.startsWith('Synced') ? '#10b981' : '#f59e0b' }}>
          {message}
        </span>
      )}
      <button 
        className="btn" 
        onClick={handleSync} 
        disabled={syncing}
        style={{
          background: syncing ? '#4b5563' : 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
          color: '#fff',
          cursor: syncing ? 'not-allowed' : 'pointer'
        }}
      >
        {syncing ? 'Syncing...' : '↻ Sync Shopify Orders'}
      </button>
    </div>
  )
}
