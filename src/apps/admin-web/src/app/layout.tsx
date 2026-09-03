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
        <title>Admin Console | Distribution OS</title>
        <meta name="description" content="AI KOL Distribution OS Admin Portal" />
      </head>
      <body suppressHydrationWarning>
        <div className="sidebar">
          <div className="logo">ADMIN_CONSOLE</div>
          <Link href="/">Audit Ledger</Link>
          <Link href="/commission">Rules & Payouts</Link>
          <Link href="/analytics">AI Telemetry</Link>
        </div>
        <div className="main-content">
          {children}
        </div>
      </body>
    </html>
  )
}
