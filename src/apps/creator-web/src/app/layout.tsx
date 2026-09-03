import './globals.css'
import Link from 'next/link'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <title>Creator Studio | Distribution OS</title>
        <meta name="description" content="AI KOL Distribution OS Creator Portal" />
      </head>
      <body suppressHydrationWarning>
        <div className="container">
          <nav className="nav glass-panel" style={{ padding: '1rem 2rem', marginBottom: '2rem' }}>
            <div className="logo">STUDIO_OS</div>
            <Link href="/">Tasks</Link>
            <Link href="/assets">Assets & Links</Link>
            <Link href="/earnings">Earnings</Link>
          </nav>
          {children}
        </div>
      </body>
    </html>
  )
}
