import Link from 'next/link'

async function getTasks() {
  try {
    const apiBase = process.env.API_BASE_URL || 'http://localhost:8000'
    const res = await fetch(`${apiBase}/frontend/tasks`, { cache: 'no-store' })
    if (!res.ok) return { tasks: [] }
    return res.json()
  } catch (e) {
    return { tasks: [] }
  }
}

export default async function TasksPage() {
  const { tasks } = await getTasks()

  return (
    <main>
      <h1 className="title">Daily Tasks</h1>
      <p className="subtitle">Your approved, AI-generated marketing assignments for today.</p>

      {tasks.length === 0 ? (
        <div className="glass-panel" style={{ textAlign: 'center', padding: '3.5rem 1rem' }}>
          <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>⏳</div>
          <h3 style={{ margin: 0, fontSize: '1.25rem' }}>No Tasks Published Yet</h3>
          <p style={{ color: 'var(--text-secondary)', maxWidth: '520px', margin: '0.75rem auto 1.5rem auto', lineHeight: 1.5 }}>
            New campaigns appear here immediately after your Merchant Admin reviews and publishes them from the AI Content Studio.
          </p>
          <Link href="/assets" className="btn" style={{ textDecoration: 'none', display: 'inline-block' }}>
            View Tracking Links & Codes &gt;
          </Link>
        </div>
      ) : (
        <div className="grid">
          {tasks.map((task: any) => (
            <div key={task.job_id} className="glass-panel">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                <span style={{
                  background: 'rgba(16, 185, 129, 0.15)',
                  color: '#10b981',
                  padding: '0.25rem 0.65rem',
                  borderRadius: '9999px',
                  fontSize: '0.75rem',
                  fontWeight: 700
                }}>
                  ● READY TO POST
                </span>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                  {task.created_at ? new Date(task.created_at).toLocaleDateString() : 'Today'}
                </span>
              </div>

              <h3 style={{ margin: '0 0 0.5rem 0' }}>
                Promote: {task.product_title || 'Shopify Product'}
              </h3>
              
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '1.25rem', lineHeight: 1.5 }}>
                {task.visual_hook ? `"${task.visual_hook.substring(0, 90)}..."` : '9:16 vertical video and script approved for posting.'}
              </p>

              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <Link href="/assets" className="btn" style={{ textDecoration: 'none', flex: 1, textAlign: 'center' }}>
                  View Asset & Download &gt;
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </main>
  )
}
