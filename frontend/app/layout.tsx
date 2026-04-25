import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Debate Orchestrator',
  description: 'Voice-first AI debate platform with live crowd scoring and AI verdicts',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-bg text-ink min-h-screen antialiased font-sans">
        {children}
      </body>
    </html>
  )
}
