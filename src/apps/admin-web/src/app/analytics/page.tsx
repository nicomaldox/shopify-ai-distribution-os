async function getMetrics() {
  try {
    const res = await fetch('http://core-api:8000/frontend/ai-metrics', { cache: 'no-store' });
    if (!res.ok) return { metrics: { total_tokens: 0, cost_usd: 0, accuracy: 1.0 }, logs: [] };
    return res.json();
  } catch (e) {
    return { metrics: { total_tokens: 0, cost_usd: 0, accuracy: 1.0 }, logs: [] };
  }
}

export default async function AnalyticsPage() {
  const { metrics, logs } = await getMetrics();

  return (
    <main>
      <h1 className="title">AI Telemetry & ROI</h1>
      <p className="subtitle">Track token usage, cost, and claims accuracy from ai_generation_logs.</p>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.5rem', marginBottom: '2rem' }}>
        <div className="glass-panel">
          <h4 style={{ color: 'var(--text-secondary)', margin: '0 0 0.5rem 0' }}>Total Tokens Spent</h4>
          <h2 style={{ fontSize: '2rem', margin: 0 }}>{metrics.total_tokens.toLocaleString()}</h2>
        </div>
        <div className="glass-panel">
          <h4 style={{ color: 'var(--text-secondary)', margin: '0 0 0.5rem 0' }}>Est. Inference Cost</h4>
          <h2 style={{ fontSize: '2rem', margin: 0, color: '#ef4444' }}>${metrics.cost_usd.toFixed(4)}</h2>
        </div>
        <div className="glass-panel">
          <h4 style={{ color: 'var(--text-secondary)', margin: '0 0 0.5rem 0' }}>Claims Accuracy</h4>
          <h2 style={{ fontSize: '2rem', margin: 0, color: '#10b981' }}>{(metrics.accuracy * 100).toFixed(1)}%</h2>
        </div>
      </div>

      <div className="glass-panel">
        <h3>Recent AI Generations</h3>
        <table>
          <thead>
            <tr>
              <th>Trace ID</th>
              <th>Duration (ms)</th>
              <th>Tokens</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {logs.length === 0 ? (
              <tr><td colSpan={4} style={{textAlign: 'center'}}>No generation logs found.</td></tr>
            ) : (
              logs.map((row: any) => (
                <tr key={row.trace_id}>
                  <td><code>{row.trace_id}</code></td>
                  <td>{row.latency_ms}</td>
                  <td>{row.total_tokens}</td>
                  <td>
                    <span style={{ color: row.status === 'SUCCESS' ? '#10b981' : '#ef4444', fontWeight: 600 }}>
                      {row.status}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </main>
  )
}
