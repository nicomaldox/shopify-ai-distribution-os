async function getEarnings() {
  try {
    const apiBase = process.env.API_BASE_URL || 'http://localhost:8000'
    const res = await fetch(`${apiBase}/frontend/earnings`, { cache: 'no-store' });
    if (!res.ok) return { data: [] };
    return res.json();
  } catch (e) {
    return { data: [] };
  }
}

export default async function EarningsPage() {
  const { data } = await getEarnings();
  
  let available = 0;
  let pending = 0;
  
  data.forEach((row: any) => {
    if (row.status === 'CLEARED') available += parseFloat(row.amount);
    if (row.status === 'PENDING') pending += parseFloat(row.amount);
  });

  return (
    <main>
      <h1 className="title">Real-Time Earnings</h1>
      <p className="subtitle">Your immutable commission ledger synced with Shopify.</p>
      
      <div className="grid" style={{ marginBottom: '2rem' }}>
        <div className="glass-panel">
          <p style={{ color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Available Balance</p>
          <h2 style={{ fontSize: '2.5rem', margin: 0, color: '#10b981' }}>+NT$ {available.toFixed(2)}</h2>
        </div>
        <div className="glass-panel">
          <p style={{ color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Pending (7-day hold)</p>
          <h2 style={{ fontSize: '2.5rem', margin: 0, color: '#f59e0b' }}>+NT$ {pending.toFixed(2)}</h2>
        </div>
      </div>

      <div className="glass-panel">
        <h3>Recent Transactions</h3>
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Type</th>
              <th>Amount (NTD)</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {data.length === 0 ? (
              <tr><td colSpan={4} style={{textAlign: 'center'}}>No transactions yet.</td></tr>
            ) : (
              data.map((row: any) => (
                <tr key={row.ledger_id}>
                  <td>{row.date}</td>
                  <td>
                    <span style={{ color: row.transaction_type === 'EARN' ? '#10b981' : '#ef4444', fontWeight: 600 }}>
                      {row.transaction_type}
                    </span>
                  </td>
                  <td>{parseFloat(row.amount) > 0 ? '+' : ''}{parseFloat(row.amount).toFixed(2)}</td>
                  <td>{row.status}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </main>
  )
}
