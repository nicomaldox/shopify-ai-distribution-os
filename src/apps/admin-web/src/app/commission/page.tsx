export default function CommissionPage() {
  return (
    <main>
      <h1 className="title">Commission Rules</h1>
      <p className="subtitle">Manage default global payout percentages and overrides.</p>
      
      <div className="glass-panel" style={{ maxWidth: '600px' }}>
        <h3>Global Default Rate</h3>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
          This percentage applies to all creators unless an override exists. Current PoC default is 20%.
        </p>
        
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <input 
            type="number" 
            defaultValue={20} 
            style={{ 
              background: 'rgba(0,0,0,0.5)', 
              border: '1px solid var(--panel-border)', 
              color: 'white', 
              padding: '0.75rem', 
              borderRadius: '6px',
              fontSize: '1.125rem',
              width: '100px'
            }} 
          />
          <span style={{ fontSize: '1.25rem', color: 'var(--text-secondary)' }}>%</span>
          <button className="btn" style={{ marginLeft: 'auto' }}>Save Rule</button>
        </div>
      </div>

      <div className="glass-panel">
        <h3>Creator Overrides</h3>
        <table>
          <thead>
            <tr>
              <th>Creator Code</th>
              <th>Custom Rate (%)</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td colSpan={4} style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
                No active overrides.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </main>
  )
}
