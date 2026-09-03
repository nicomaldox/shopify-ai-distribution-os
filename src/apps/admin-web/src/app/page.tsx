import SyncButton from '@/components/SyncButton'

async function getLedger() {
  try {
    const apiBase = process.env.API_BASE_URL || 'http://localhost:8000'
    const res = await fetch(`${apiBase}/frontend/audit-ledger`, { cache: 'no-store' });
    if (!res.ok) return { data: [] };
    return res.json();
  } catch (e) {
    return { data: [] };
  }
}

export default async function LedgerPage() {
  const { data } = await getLedger();

  return (
    <main>
      <h1 className="title">Live Audit Ledger</h1>
      <p className="subtitle">Immutable view of all commission transactions (PostgreSQL layer).</p>
      
      <div className="glass-panel">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3>Transaction Stream</h3>
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
            <SyncButton />
            <button className="btn">Export CSV</button>
          </div>
        </div>
        <table>
          <thead>
            <tr>
              <th>ID (UUID)</th>
              <th>Order ID</th>
              <th>Order Total (Net)</th>
              <th>Type</th>
              <th>Commission (20%)</th>
              <th>Status</th>
              <th>Timestamp (Local)</th>
            </tr>
          </thead>
          <tbody>
            {data.length === 0 ? (
              <tr><td colSpan={7} style={{textAlign: 'center', padding: '2rem'}}>No transactions found.</td></tr>
            ) : (
              data.map((row: any) => {
                const orderTotal = row.order_total ? parseFloat(row.order_total) : 0;
                const commission = parseFloat(row.amount);
                return (
                  <tr key={row.ledger_id}>
                    <td><code>{row.ledger_id.substring(0,8)}...</code></td>
                    <td style={{ fontFamily: 'monospace' }}>{row.order_id || 'N/A'}</td>
                    <td>{orderTotal > 0 ? `NT$ ${orderTotal.toFixed(2)}` : '—'}</td>
                    <td>
                      <span style={{ color: row.transaction_type === 'EARN' ? '#10b981' : '#ef4444', fontWeight: 600 }}>
                        {row.transaction_type}
                      </span>
                    </td>
                    <td style={{ fontWeight: 600, color: commission >= 0 ? '#10b981' : '#ef4444' }}>
                      {commission > 0 ? '+NT$ ' : '-NT$ '}{Math.abs(commission).toFixed(2)}
                    </td>
                    <td>
                      <span style={{
                        padding: '0.2rem 0.6rem',
                        borderRadius: '9999px',
                        fontSize: '0.75rem',
                        background: row.status === 'CLEARED' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                        color: row.status === 'CLEARED' ? '#10b981' : '#f59e0b',
                        fontWeight: 500
                      }}>
                        {row.status}
                      </span>
                    </td>
                    <td style={{ whiteSpace: 'nowrap' }}>{row.date}</td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>
    </main>
  )
}
