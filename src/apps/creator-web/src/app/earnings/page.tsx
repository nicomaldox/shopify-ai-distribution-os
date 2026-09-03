import SyncButton from '@/components/SyncButton'

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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
        <div>
          <h1 className="title" style={{ marginBottom: '0.25rem' }}>Real-Time Earnings</h1>
          <p className="subtitle">Your immutable 20% commission ledger synced directly with Shopify.</p>
        </div>
        <SyncButton />
      </div>
      
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
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3 style={{ margin: 0 }}>Recent Commission Transactions</h3>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Commission Rate: <strong style={{ color: '#6366f1' }}>20%</strong>
          </span>
        </div>
        <table>
          <thead>
            <tr>
              <th>Date & Time</th>
              <th>Order ID</th>
              <th>Customer Paid (Net)</th>
              <th>Type</th>
              <th>Your Commission (20%)</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {data.length === 0 ? (
              <tr><td colSpan={6} style={{textAlign: 'center', padding: '2rem'}}>No transactions yet. Place an order on Shopify to test!</td></tr>
            ) : (
              data.map((row: any) => {
                const orderTotal = row.order_total ? parseFloat(row.order_total) : 0;
                const commission = parseFloat(row.amount);
                return (
                  <tr key={row.ledger_id}>
                    <td style={{ whiteSpace: 'nowrap' }}>{row.date}</td>
                    <td style={{ fontFamily: 'monospace', color: 'var(--text-secondary)' }}>
                      {row.order_id || 'N/A'}
                    </td>
                    <td>
                      {orderTotal > 0 ? `NT$ ${orderTotal.toFixed(2)}` : '—'}
                    </td>
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
