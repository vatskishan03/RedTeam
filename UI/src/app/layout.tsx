import type { Metadata } from 'next'
import { Inter, JetBrains_Mono } from 'next/font/google'
import './globals.css'

const inter = Inter({ 
  subsets: ['latin'],
  variable: '--font-inter',
})

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-mono',
})

export const metadata: Metadata = {
  title: 'Red Team Code Auditor | AI Security Analysis',
  description: 'Multi-agent AI system that attacks your code to find vulnerabilities before real hackers do. Watch AI agents debate security in real-time.',
  keywords: ['security', 'code audit', 'AI', 'multi-agent', 'vulnerability', 'penetration testing'],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="bg-bg-primary text-text-primary min-h-screen antialiased">
        {children}
      </body>
    </html>
  )
}
