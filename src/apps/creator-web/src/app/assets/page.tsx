export default function AssetsPage() {
  return (
    <main>
      <h1 className="title">Assets & Links</h1>
      <p className="subtitle">Download your AI videos and copy your unique tracking codes.</p>
      
      <div className="glass-panel" style={{ marginBottom: '2rem' }}>
        <h2>Your Active Tracking Links</h2>
        <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem', alignItems: 'center' }}>
          <code style={{ background: 'rgba(0,0,0,0.5)', padding: '1rem', borderRadius: '8px', flex: 1, border: '1px solid var(--panel-border)' }}>
            https://go.brand.com/r/alex
          </code>
          <button className="btn">Copy Link</button>
        </div>
        <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem', alignItems: 'center' }}>
          <code style={{ background: 'rgba(0,0,0,0.5)', padding: '1rem', borderRadius: '8px', flex: 1, border: '1px solid var(--panel-border)', color: 'var(--accent-color)', fontWeight: 'bold' }}>
            PROMO CODE: ALEX10
          </code>
          <button className="btn">Copy Code</button>
        </div>
      </div>

      <div className="grid">
        <div className="glass-panel">
          <div style={{ height: '200px', background: 'rgba(0,0,0,0.5)', borderRadius: '8px', marginBottom: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ color: 'var(--text-secondary)' }}>9:16 Video Preview</span>
          </div>
          <h3>Shopify Cap - TikTok Ad</h3>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Generated today • 00:20</p>
          <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
            <button className="btn" style={{ flex: 1 }}>Download .mp4</button>
            <button className="btn" style={{ flex: 1, background: 'transparent', border: '1px solid var(--panel-border)' }}>Copy Script</button>
          </div>
        </div>
      </div>
    </main>
  )
}
