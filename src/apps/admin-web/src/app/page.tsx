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
              <th>Creator ID</th>
              <th>Order ID</th>
              <th>Type</th>
              <th>Amount (NTD)</th>
              <th>Status</th>
              <th>Timestamp</th>
            </tr>
          </thead>
          <tbody>
            {data.length === 0 ? (
              <tr><td colSpan={7} style={{textAlign: 'center'}}>No transactions found.</td></tr>
            ) : (
              data.map((row: any) => (
                <tr key={row.ledger_id}>
                  <td><code>{row.ledger_id.substring(0,8)}...</code></td>
                  <td>{row.creator_id ? row.creator_id.substring(0,8) : 'N/A'}</td>
                  <td>{row.order_id}</td>
                  <td>
                    <span style={{ color: row.transaction_type === 'EARN' ? '#10b981' : '#ef4444', fontWeight: 600 }}>
                      {row.transaction_type}
                    </span>
                  </td>
                  <td>{parseFloat(row.amount).toFixed(4)}</td>
                  <td>{row.status}</td>
                  <td>{row.date}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </main>
  )
}
