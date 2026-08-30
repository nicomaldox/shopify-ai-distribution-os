import type { Metadata } from 'next'
import './globals.css'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'Admin Console | Distribution OS',
  description: 'AI KOL Distribution OS Admin Portal',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
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
