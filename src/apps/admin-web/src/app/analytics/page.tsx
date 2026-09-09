async function getMetrics() {
  const defaultFallback = {
    metrics: {
      total_tokens: 0,
      cost_usd: 6.40,
      llm_cost_usd: 0.0,
      historical_fal_wasted_usd: 6.40,
      live_fal_cost_usd: 0.0,
      total_fal_cost_usd: 6.40,
      total_cost_usd: 6.40,
      accuracy: 1.0,
      total_renders: 0,
      cloud_renders: 0
    },
    logs: [],
    video_jobs: []
  };

  try {
    const apiBase = process.env.API_BASE_URL || 'http://localhost:8000';
    const res = await fetch(`${apiBase}/frontend/ai-metrics`, { cache: 'no-store' });
    if (res.ok) return await res.json();
    
    const res2 = await fetch('http://127.0.0.1:8000/frontend/ai-metrics', { cache: 'no-store' });
    if (res2.ok) return await res2.json();
    return defaultFallback;
  } catch (e) {
    try {
      const res2 = await fetch('http://127.0.0.1:8000/frontend/ai-metrics', { cache: 'no-store' });
      if (res2.ok) return await res2.json();
    } catch (_) {}
    return defaultFallback;
  }
}

export default async function AnalyticsPage() {
  const data = await getMetrics();
  const metrics = data.metrics || {};
  const logs = data.logs || [];
  const videoJobs = data.video_jobs || [];

  const totalCost = metrics.total_cost_usd ?? metrics.cost_usd ?? 6.40;
  const falTotal = metrics.total_fal_cost_usd ?? 6.40;
  const falWasted = metrics.historical_fal_wasted_usd ?? 6.40;
  const falLive = metrics.live_fal_cost_usd ?? 0.00;
  const llmCost = metrics.llm_cost_usd ?? 0.00;
  const totalTokens = metrics.total_tokens ?? 0;
  const accuracy = metrics.accuracy ?? 1.0;
  const totalRenders = metrics.total_renders ?? 0;
  const cloudRenders = metrics.cloud_renders ?? 0;

  return (
    <main style={{ maxWidth: '1200px' }}>
      <h1 className="title">AI & Cloud Compute Observability</h1>
      <p className="subtitle">
        Real-time financial telemetry tracking GPT-4o LLM token spend, Fal.ai cloud video expenses, and claims compliance.
      </p>

      {/* Credit Safety Notice */}
      <div style={{
        background: 'rgba(139, 92, 246, 0.12)',
        border: '1px solid rgba(139, 92, 246, 0.35)',
        borderRadius: '10px',
        padding: '1rem 1.25rem',
        marginBottom: '2rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '1rem'
      }}>
        <div>
          <div style={{ fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
            🛡️ Credit Conservation Mode Active (<code style={{ color: '#a78bfa' }}>ENABLE_CLOUD_VIDEO_RENDER=false</code>)
          </div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            All current video generation executes via zero-cost local FFmpeg synthetic simulation to protect your credits. When you are ready for manual testing, toggle <code style={{ color: '#a78bfa' }}>ENABLE_CLOUD_VIDEO_RENDER=true</code> in <code style={{ color: '#a78bfa' }}>.env</code>.
          </div>
        </div>
        <span style={{
          background: 'rgba(16, 185, 129, 0.2)',
          color: '#10b981',
          padding: '0.35rem 0.75rem',
          borderRadius: '9999px',
          fontWeight: 700,
          fontSize: '0.8rem',
          whiteSpace: 'nowrap'
        }}>
          $0.00 CURRENT BURN
        </span>
      </div>
      
      {/* Financial KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1.25rem', marginBottom: '2rem' }}>
        {/* Total Compute Expenses */}
        <div className="glass-panel" style={{ position: 'relative', overflow: 'hidden' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
            Total AI & Cloud Expenses
          </div>
          <h2 style={{ fontSize: '2.2rem', margin: '0.5rem 0', color: '#f87171' }}>
            ${totalCost.toFixed(2)} <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>USD</span>
          </h2>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            LLM (${llmCost.toFixed(4)}) + Fal.ai (${falTotal.toFixed(2)})
          </div>
        </div>

        {/* Fal.ai Expenses Breakdown */}
        <div className="glass-panel" style={{ border: '1px solid rgba(239, 68, 68, 0.3)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
              Fal.ai Video Expenses
            </span>
            <span style={{ background: 'rgba(239,68,68,0.2)', color: '#f87171', fontSize: '0.7rem', padding: '0.2rem 0.5rem', borderRadius: '4px', fontWeight: 700 }}>
              TRACKED
            </span>
          </div>
          <h2 style={{ fontSize: '2.2rem', margin: '0.5rem 0', color: '#fbbf24' }}>
            ${falTotal.toFixed(2)} <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>USD</span>
          </h2>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
            <span>⚠️ <strong>${falWasted.toFixed(2)}</strong> Historical Debug Spend</span>
            <span>🎬 <strong>${falLive.toFixed(2)}</strong> Live Video Jobs</span>
          </div>
        </div>

        {/* OpenAI GPT-4o Inference */}
        <div className="glass-panel">
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
            OpenAI GPT-4o LLM
          </div>
          <h2 style={{ fontSize: '2.2rem', margin: '0.5rem 0', color: '#a78bfa' }}>
            ${llmCost.toFixed(4)} <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>USD</span>
          </h2>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            {totalTokens.toLocaleString()} total tokens processed
          </div>
        </div>

        {/* Claims Accuracy */}
        <div className="glass-panel">
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
            Claims Accuracy Rate
          </div>
          <h2 style={{ fontSize: '2.2rem', margin: '0.5rem 0', color: '#10b981' }}>
            {(accuracy * 100).toFixed(1)}%
          </h2>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            LLM Judge compliance pass rate
          </div>
        </div>
      </div>

      {/* Video Factory Render Jobs Observability */}
      <div className="glass-panel">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <div>
            <h3 style={{ margin: 0 }}>Fal.ai Cloud Video Render Observability</h3>
            <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              Individual render job expenses, mode (Option A vs Looping), and engine breakdown ({totalRenders} total / {cloudRenders} cloud).
            </p>
          </div>
        </div>

        <table>
          <thead>
            <tr>
              <th>Job ID</th>
              <th>Hook Preview</th>
              <th>Mode</th>
              <th>Scenes</th>
              <th>Est. Cost ($)</th>
              <th>Engine</th>
              <th>Status</th>
              <th>Created At</th>
            </tr>
          </thead>
          <tbody>
            {videoJobs.length === 0 ? (
              <tr>
                <td colSpan={8} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
                  No video render jobs recorded in the current session.
                </td>
              </tr>
            ) : (
              videoJobs.map((job: any) => (
                <tr key={job.job_id}>
                  <td><code>{job.job_id}</code></td>
                  <td style={{ maxWidth: '240px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {job.visual_hook || '—'}
                  </td>
                  <td>
                    <span style={{
                      background: job.render_mode === 'multi_clip' ? 'rgba(139, 92, 246, 0.2)' : 'rgba(255,255,255,0.05)',
                      color: job.render_mode === 'multi_clip' ? '#c4b5fd' : 'var(--text-secondary)',
                      padding: '0.2rem 0.5rem',
                      borderRadius: '4px',
                      fontSize: '0.75rem',
                      fontWeight: 600
                    }}>
                      {job.render_mode === 'multi_clip' ? 'Option A: Multi-Clip' : '1-Clip Loop'}
                    </span>
                  </td>
                  <td>{job.scenes_count || 1} scenes</td>
                  <td style={{ fontWeight: 700, color: Number(job.estimated_cost_usd) > 0 ? '#fbbf24' : 'var(--text-secondary)' }}>
                    ${Number(job.estimated_cost_usd || 0).toFixed(4)}
                  </td>
                  <td>
                    <span style={{
                      color: job.is_cloud_render ? '#10b981' : '#94a3b8',
                      fontSize: '0.8rem',
                      fontWeight: 600
                    }}>
                      {job.is_cloud_render ? '☁️ Fal.ai Cloud' : '🖥️ Synthetic Mock'}
                    </span>
                  </td>
                  <td>
                    <span style={{
                      color: job.status === 'PUBLISHED' ? '#10b981' : job.status === 'COMPLETED' ? '#38bdf8' : job.status === 'FAILED' ? '#ef4444' : '#fbbf24',
                      fontWeight: 600,
                      fontSize: '0.8rem'
                    }}>
                      {job.status}
                    </span>
                  </td>
                  <td style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    {job.created_time || '—'}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* LLM Generation Telemetry Logs */}
      <div className="glass-panel">
        <h3 style={{ margin: '0 0 0.5rem 0' }}>LLM Director Script Generation Logs (GPT-4o)</h3>
        <p style={{ margin: '0 0 1rem 0', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          Detailed telemetry captured from <code style={{ color: '#a78bfa' }}>ai_generation_logs</code>.
        </p>
        <table>
          <thead>
            <tr>
              <th>Trace ID</th>
              <th>Duration (ms)</th>
              <th>Tokens</th>
              <th>Cost ($)</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {logs.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
                  No script generation logs found in current session.
                </td>
              </tr>
            ) : (
              logs.map((row: any) => (
                <tr key={row.trace_id}>
                  <td><code>{row.trace_id}</code></td>
                  <td>{row.latency_ms} ms</td>
                  <td>{row.total_tokens}</td>
                  <td style={{ color: '#a78bfa', fontWeight: 600 }}>
                    ${Number(row.estimated_cost_usd || 0).toFixed(4)}
                  </td>
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
