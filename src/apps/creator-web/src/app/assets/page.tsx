import React from 'react'
import CopyableButton from '@/components/CopyableButton'

async function getPublishedAssets() {
  try {
    const apiBase = process.env.API_BASE_URL || 'http://localhost:8000'
    const res = await fetch(`${apiBase}/frontend/tasks`, { cache: 'no-store' })
    if (!res.ok) return { tasks: [] }
    return res.json()
  } catch (e) {
    return { tasks: [] }
  }
}

export default async function AssetsPage() {
  const { tasks } = await getPublishedAssets()
  const apiBase = process.env.API_BASE_URL || 'http://localhost:8000'

  return (
    <main style={{ maxWidth: '1000px', margin: '0 auto' }}>
      <h1 className="title">Assets & Links</h1>
      <p className="subtitle">Download your AI videos, copy your scripts, and use your unique tracking codes.</p>
      
      {/* Tracking Center */}
      <div className="glass-panel" style={{ marginBottom: '2.5rem' }}>
        <h2 style={{ fontSize: '1.25rem', marginBottom: '1rem' }}>Your Active Attribution Credentials</h2>
        
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.4rem', fontWeight: 600 }}>
              PERSONAL TRACKING LINK
            </div>
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <code style={{ background: 'rgba(0,0,0,0.5)', padding: '0.75rem', borderRadius: '6px', flex: 1, border: '1px solid var(--panel-border)', fontSize: '0.9rem' }}>
                https://go.brand.com/r/elena-glow
              </code>
              <CopyableButton textToCopy="https://go.brand.com/r/elena-glow" label="Copy Link" />
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.4rem', fontWeight: 600 }}>
              EXCLUSIVE DISCOUNT COUPON
            </div>
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <code style={{ background: 'rgba(0,0,0,0.5)', padding: '0.75rem', borderRadius: '6px', flex: 1, border: '1px solid var(--panel-border)', color: 'var(--accent-color)', fontWeight: 'bold', fontSize: '0.9rem' }}>
                PROMO CODE: ELENA10
              </code>
              <CopyableButton textToCopy="ELENA10" label="Copy Code" />
            </div>
          </div>
        </div>
      </div>

      <h2 style={{ fontSize: '1.25rem', marginBottom: '1.25rem' }}>Approved Video Deliverables</h2>

      {tasks.length === 0 ? (
        <div className="glass-panel" style={{ textAlign: 'center', padding: '3.5rem 1rem' }}>
          <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>🎬</div>
          <h3 style={{ margin: 0, fontSize: '1.25rem' }}>No Approved Videos Ready</h3>
          <p style={{ color: 'var(--text-secondary)', maxWidth: '520px', margin: '0.75rem auto 0 auto', lineHeight: 1.5 }}>
            Videos are reviewed for quality by the Brand Admin in the Content Studio before publishing here. Check back shortly!
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          {tasks.map((task: any) => {
            const videoSrc = task.video_url ? (task.video_url.startsWith('http') ? task.video_url : `${apiBase}${task.video_url}`) : null
            const fullPostText = `${task.narration_text || ''}\n\nShop with my code ALEX10 for 10% off! Link in bio: https://go.brand.com/r/alex\n\n${task.ad_disclosures || '#Ad #AffiliateLink'}`

            return (
              <div key={task.job_id} className="glass-panel" style={{ padding: '2rem' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: '2rem' }}>
                  {/* 9:16 Video Player */}
                  <div style={{
                    background: 'black',
                    borderRadius: '12px',
                    overflow: 'hidden',
                    border: '1px solid var(--panel-border)',
                    height: '460px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    {videoSrc ? (
                      <video
                        src={videoSrc}
                        controls
                        loop
                        playsInline
                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      />
                    ) : (
                      <div style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: '1rem' }}>
                        Preview Loading...
                      </div>
                    )}
                  </div>

                  {/* Asset Details & Copy Actions */}
                  <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                        <span style={{
                          background: 'rgba(16, 185, 129, 0.15)',
                          color: '#10b981',
                          padding: '0.2rem 0.6rem',
                          borderRadius: '9999px',
                          fontSize: '0.75rem',
                          fontWeight: 700
                        }}>
                          ● PUBLISHED & VERIFIED
                        </span>
                        <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                          Job: <code>{task.job_id}</code>
                        </span>
                      </div>

                      <h3 style={{ margin: '0.5rem 0' }}>{task.product_title || 'Shopify Product'} — 9:16 UGC Video</h3>
                      
                      <div style={{ background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--panel-border)', margin: '1rem 0' }}>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.25rem', fontWeight: 600 }}>
                          APPROVED SCRIPT & NARRATION
                        </div>
                        <p style={{ margin: 0, fontSize: '0.9rem', lineHeight: 1.5, color: '#f8fafc' }}>
                          &quot;{task.narration_text}&quot;
                        </p>
                      </div>

                      <div style={{ background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--panel-border)', marginBottom: '1.5rem' }}>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.25rem', fontWeight: 600 }}>
                          RECOMMENDED POST CAPTION (WITH DISCLOSURES)
                        </div>
                        <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-secondary)', whiteSpace: 'pre-line' }}>
                          {fullPostText}
                        </p>
                      </div>
                    </div>

                    {/* Download & Copy Buttons */}
                    <div style={{ display: 'flex', gap: '1rem' }}>
                      {videoSrc && (
                        <a
                          href={videoSrc}
                          download={`creator_video_${task.job_id}.mp4`}
                          target="_blank"
                          rel="noreferrer"
                          className="btn"
                          style={{
                            flex: 1,
                            textDecoration: 'none',
                            textAlign: 'center',
                            background: '#10b981',
                            padding: '0.75rem 1rem'
                          }}
                        >
                          ⬇️ Download .MP4 Video
                        </a>
                      )}
                      
                      <CopyableButton
                        textToCopy={fullPostText}
                        label="📋 Copy Caption & Script"
                        copiedLabel="Copied to Clipboard! ✓"
                        style={{ flex: 1, padding: '0.75rem 1rem' }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </main>
  )
}
