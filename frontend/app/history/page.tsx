'use client'
import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { useRouter } from 'next/navigation'
import { api } from '@/lib/api'
import type { DebateListItem } from '@/lib/api'
import { DebateCard } from '@/components/DebateCard'

export default function HistoryPage() {
  const router = useRouter()
  const [debates, setDebates] = useState<DebateListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .listDebates()
      .then(setDebates)
      .catch(e => setError((e as Error).message))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="min-h-screen bg-bg">
      {/* Nav */}
      <nav className="flex items-center px-8 py-4 border-b border-white/[0.07] sticky top-0 bg-bg/90 backdrop-blur-xl z-10">
        <button
          onClick={() => router.push('/')}
          className="font-display font-bold text-xl tracking-tight"
        >
          Debate<span className="text-cta">.</span>
        </button>
        <div className="flex-1" />
        <button
          onClick={() => router.push('/debate/setup')}
          className="text-sm font-semibold text-cta hover:opacity-80 px-4 py-1.5 rounded-full border border-cta/30 hover:border-cta/50 transition-all"
        >
          + New Debate
        </button>
      </nav>

      <div className="max-w-3xl mx-auto px-6 py-12">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-10"
        >
          <h1 className="font-display font-bold text-4xl tracking-tight mb-2">Past Debates</h1>
          <p className="text-muted">Click any debate to view its full verdict and summary.</p>
        </motion.div>

        {loading && (
          <div className="flex justify-center py-24">
            <div className="w-8 h-8 rounded-full border-2 border-white/10 border-t-cta animate-spin" />
          </div>
        )}

        {error && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="bg-danger/10 border border-danger/25 rounded-xl p-4 text-red-400 text-sm"
          >
            {error}
          </motion.div>
        )}

        {!loading && !error && (
          <div className="flex flex-col gap-3">
            {debates.map((d, i) => (
              <DebateCard key={d.id} debate={d} index={i} />
            ))}

            {debates.length === 0 && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-center py-24 text-muted"
              >
                No debates yet.{' '}
                <button
                  onClick={() => router.push('/debate/setup')}
                  className="text-cta hover:underline"
                >
                  Start one →
                </button>
              </motion.div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
