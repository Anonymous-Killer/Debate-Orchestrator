'use client'
import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useRouter } from 'next/navigation'
import { api } from '@/lib/api'

export default function SetupPage() {
  const router = useRouter()
  const [form, setForm] = useState({ topic: '', sideA: '', sideB: '', stanceA: 'For', stanceB: 'Against' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  function set(k: keyof typeof form, v: string) {
    setForm(f => ({ ...f, [k]: v }))
  }

  async function handleStart() {
    const missing = !form.topic.trim() || !form.sideA.trim() || !form.sideB.trim()
    if (missing) { setError('Please fill in topic and both side names.'); return }
    setError('')
    setLoading(true)
    try {
      const debate = await api.createDebate({
        topic: form.topic.trim(),
        participant_a_id: form.sideA.trim(),
        participant_b_id: form.sideB.trim(),
      })
      await api.startDebate(debate.id, {
        stance_a: form.stanceA.trim() || 'For',
        stance_b: form.stanceB.trim() || 'Against',
        active_side: 'A',
      })
      const params = new URLSearchParams({
        id:    debate.id,
        a:     form.sideA.trim(),
        b:     form.sideB.trim(),
        topic: form.topic.trim(),
      })
      router.push(`/debate/live?${params}`)
    } catch (e) {
      setError((e as Error).message ?? 'Failed to start debate.')
      setLoading(false)
    }
  }

  const inputCls =
    'w-full bg-white/[0.04] border border-white/[0.07] focus:border-cta focus:ring-2 focus:ring-cta/20 rounded-xl px-4 py-3 text-ink placeholder-muted/50 outline-none transition-all font-sans text-sm'

  return (
    <div className="min-h-screen bg-bg">
      {/* Nav */}
      <nav className="flex items-center px-8 py-4 border-b border-white/[0.07]">
        <button
          onClick={() => router.push('/')}
          className="font-display font-bold text-xl tracking-tight"
        >
          Debate<span className="text-cta">.</span>
        </button>
      </nav>

      <div className="max-w-lg mx-auto px-6 py-16">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-10"
        >
          <span
            className="text-xs font-semibold px-3 py-1 rounded-full tracking-widest uppercase mb-4 inline-block"
            style={{ background: 'rgba(124,92,252,0.15)', color: '#7c5cfc' }}
          >
            New Debate
          </span>
          <h1 className="font-display font-bold text-4xl tracking-tight mt-4 mb-3">Set the stage</h1>
          <p className="text-muted leading-relaxed">
            Define the topic, name each side, and let the argument begin.
          </p>
        </motion.div>

        {/* Form card */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-card border border-white/[0.07] rounded-2xl p-6 flex flex-col gap-5"
        >
          {/* Topic */}
          <div className="flex flex-col gap-2">
            <label className="text-xs font-semibold text-muted tracking-widest uppercase">
              Topic
            </label>
            <input
              className={inputCls}
              value={form.topic}
              onChange={e => set('topic', e.target.value)}
              placeholder="e.g. Should AI replace human judges?"
              onKeyDown={e => e.key === 'Enter' && handleStart()}
            />
          </div>

          <div className="h-px bg-white/[0.07]" />

          {/* Sides */}
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-2">
              <label
                className="text-xs font-semibold tracking-widest uppercase"
                style={{ color: '#e87848' }}
              >
                Side A — Name
              </label>
              <input
                className={inputCls}
                value={form.sideA}
                onChange={e => set('sideA', e.target.value)}
                placeholder="Alex"
              />
            </div>
            <div className="flex flex-col gap-2">
              <label
                className="text-xs font-semibold tracking-widest uppercase"
                style={{ color: '#48a8e0' }}
              >
                Side B — Name
              </label>
              <input
                className={inputCls}
                value={form.sideB}
                onChange={e => set('sideB', e.target.value)}
                placeholder="Jordan"
              />
            </div>
          </div>

          <div className="h-px bg-white/[0.07]" />

          {/* Stances */}
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-2">
              <label
                className="text-xs font-semibold tracking-widest uppercase"
                style={{ color: '#e87848' }}
              >
                Side A — Stance
              </label>
              <input
                className={inputCls}
                value={form.stanceA}
                onChange={e => set('stanceA', e.target.value)}
                placeholder="For"
              />
            </div>
            <div className="flex flex-col gap-2">
              <label
                className="text-xs font-semibold tracking-widest uppercase"
                style={{ color: '#48a8e0' }}
              >
                Side B — Stance
              </label>
              <input
                className={inputCls}
                value={form.stanceB}
                onChange={e => set('stanceB', e.target.value)}
                placeholder="Against"
              />
            </div>
          </div>
        </motion.div>

        {/* Error */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-3 bg-danger/10 border border-danger/25 rounded-xl px-4 py-3 text-red-400 text-sm"
            >
              {error}
            </motion.div>
          )}
        </AnimatePresence>

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="mt-4"
        >
          <motion.button
            whileHover={{ scale: 1.02, boxShadow: '0 0 24px 4px rgba(124,92,252,0.35)' }}
            whileTap={{ scale: 0.97 }}
            onClick={handleStart}
            disabled={loading}
            className="w-full bg-cta text-white font-semibold text-base py-3.5 rounded-full disabled:opacity-40 flex items-center justify-center gap-2 transition-all"
          >
            {loading && (
              <div className="w-4 h-4 rounded-full border-2 border-white/30 border-t-white animate-spin" />
            )}
            {loading ? 'Starting…' : 'Start Debate →'}
          </motion.button>
          <p className="text-center text-xs text-muted mt-3">
            Side A argues with their stance · Side B argues with theirs
          </p>
        </motion.div>
      </div>
    </div>
  )
}
