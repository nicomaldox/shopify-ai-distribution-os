export default function TasksPage() {
  return (
    <main>
      <h1 className="title">Daily Tasks</h1>
      <p className="subtitle">Your AI-generated marketing assignments for today.</p>
      
      <div className="grid">
        <div className="glass-panel">
          <h3>Promote: Shopify Cap</h3>
          <p style={{ color: 'var(--text-secondary)', margin: '1rem 0' }}>
            We've generated a 9:16 vertical video and script for you.
          </p>
          <button className="btn">View Asset &gt;</button>
        </div>
        
        <div className="glass-panel" style={{ opacity: 0.5 }}>
          <h3>Promote: Organic Coffee</h3>
          <p style={{ color: 'var(--text-secondary)', margin: '1rem 0' }}>
            Completed.
          </p>
          <button className="btn" disabled style={{ background: 'transparent', border: '1px solid var(--panel-border)' }}>Done</button>
        </div>
      </div>
    </main>
  )
}
