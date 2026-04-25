'use client'
import { useState, useEffect, Suspense } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useRouter, useParams, useSearchParams } from 'next/navigation'
import { api } from '@/lib/api'
import type { Verdict } from '@/lib/api'
import type { AnimPhase } from '@/types'
import { CrowdSplitBar } from '@/components/CrowdSplitBar'
import { AnimatedWinnerOverlay } from '@/components/AnimatedWinnerOverlay'

function SummaryPageInner() {
  const router     = useRouter()
  const { id }     = useParams<{ id: string }>()
  const params     = useSearchParams()
  const sideAName  = params.get('a') ?? 'Side A'
  const sideBName  = params.get('b') ?? 'Side B'

  const [animPhase, setAnimPhase] = useState<AnimPhase>('clash')
  const [verdict, setVerdict]     = useState<Verdict | null>(null)
  const [loadError, setLoadError] = useState('')

  useEffect(() => {
    api
      .getVerdict(id)
      .then(v => {
        // normalise strengths for display
        const strengthsMap = v.strengthsMap ?? {
          a: v.strengths?.slice(0, 2) ?? [],
          b: v.weaknesses?.slice(0, 2) ?? [],
        }
        setVerdict({ ...v, strengthsMap })
      })
      .catch(e => setLoadError((e as Error).message))

    const t1 = setTimeout(() => setAnimPhase('winner'), 1900)
    const t2 = setTimeout(() => setAnimPhase('done'),   4000)
    return () => { clearTimeout(t1); clearTimeout(t2) }
  }, [id])

  const winnerName  = verdict ? (verdict.winner === 'A' ? sideAName : sideBName) : null
  const winnerColor = verdict?.winner === 'B' ? '#48a8e0' : '#e87848'
  const loserColor  = verdict?.winner === 'B' ? '#e87848' : '#48a8e0'
  const loserName   = verdict?.winner === 'B' ? sideAName : sideBName
  const scoreA = verdict?.live_score?.side_a_percent ?? 50
  const scoreB = verdict?.live_score?.side_b_percent ?? 50
  const confidence = verdict?.confidence != null ? Math.round(verdict.confidence * 100) : null

  return (
    <div className="min-h-screen bg-bg">
      <AnimatedWinnerOverlay
        phase={animPhase}
        sideAName={sideAName}
        sideBName={sideBName}
        winnerName={winnerName}
        winnerColor={winnerColor}
      />

      <AnimatePresence>
        {animPhase === 'done' && (
          <motion.div
            key="summary"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
          >
            {/* Nav */}
            <nav className="flex items-center px-8 py-4 border-b border-white/[0.07]">
              <button
                onClick={() => router.push('/')}
                className="font-display font-bold text-xl tracking-tight"
              >
                Debate<span className="text-cta">.</span>
              </button>
              <div className="flex-1" />
              <button
                onClick={() => router.push('/history')}
                className="text-sm text-muted hover:text-ink px-4 py-1.5 rounded-full border border-white/[0.07] hover:border-white/[0.14] transition-all"
              >
                History
              </button>
            </nav>

            <div className="max-w-2xl mx-auto px-6 py-12 flex flex-col gap-5">
              {/* Load error */}
              {loadError && (
                <div className="bg-danger/10 border border-danger/25 rounded-xl p-4 text-red-400 text-sm">
                  {loadError}
                </div>
              )}

              {/* Winner card */}
              <motion.div
                initial={{ scale: 0.88, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
                className="rounded-2xl p-10 text-center"
                style={{
                  background: `linear-gradient(135deg, ${winnerColor}1a, ${winnerColor}08)`,
                  border: `1px solid ${winnerColor}44`,
                }}
              >
                <p
                  className="text-xs font-semibold tracking-widest uppercase mb-4"
                  style={{ color: winnerColor }}
                >
                  Winner
                </p>
                <h1
                  className="font-display font-extrabold tracking-tight mb-3"
                  style={{
                    fontSize: 'clamp(2rem,6vw,3.5rem)',
                    color: winnerColor,
                    textShadow: `0 0 40px ${winnerColor}55`,
                  }}
                >
                  {winnerName ?? '…'}
                </h1>
                {confidence != null && (
                  <p className="text-sm text-muted">
                    Verdict confidence: <span className="text-ink font-semibold">{confidence}%</span>
                  </p>
                )}
              </motion.div>

              {/* Score split */}
              <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="bg-card border border-white/[0.07] rounded-2xl p-5"
              >
                <p className="text-xs font-semibold text-muted tracking-widest uppercase mb-3">
                  Final Crowd Split
                </p>
                <CrowdSplitBar
                  scoreA={scoreA}
                  scoreB={scoreB}
                  nameA={sideAName}
                  nameB={sideBName}
                  size="lg"
                />
              </motion.div>

              {/* Verdict summary */}
              {verdict?.summary && (
                <motion.div
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                  className="bg-card border border-white/[0.07] rounded-2xl p-6"
                >
                  <p className="text-xs font-semibold text-muted tracking-widest uppercase mb-3">
                    Verdict
                  </p>
                  <p className="text-base leading-relaxed text-ink">{verdict.summary}</p>
                </motion.div>
              )}

              {/* Deciding factors */}
              {verdict?.deciding_factors && verdict.deciding_factors.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.25 }}
                  className="bg-card border border-white/[0.07] rounded-2xl p-6"
                >
                  <p className="text-xs font-semibold text-muted tracking-widest uppercase mb-3">
                    Deciding Factors
                  </p>
                  <ul className="flex flex-col gap-2">
                    {verdict.deciding_factors.map((f, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-ink">
                        <span className="text-cta mt-0.5">•</span>
                        <span>{f}</span>
                      </li>
                    ))}
                  </ul>
                </motion.div>
              )}

              {/* Strengths comparison */}
              {verdict?.strengthsMap && (
                <motion.div
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 }}
                  className="grid grid-cols-2 gap-4"
                >
                  {(['a', 'b'] as const).map(k => {
                    const name  = k === 'a' ? sideAName : sideBName
                    const color = k === 'a' ? '#e87848' : '#48a8e0'
                    const items = verdict.strengthsMap![k] ?? []
                    return (
                      <div
                        key={k}
                        className="bg-card border border-white/[0.07] rounded-2xl p-5"
                        style={{ borderColor: `${color}1a` }}
                      >
                        <p
                          className="text-xs font-semibold tracking-widest uppercase mb-3"
                          style={{ color }}
                        >
                          {name} — Strengths
                        </p>
                        <ul className="flex flex-col gap-1.5">
                          {items.length > 0
                            ? items.map((s, i) => (
                                <li key={i} className="text-sm text-muted leading-snug flex gap-2">
                                  <span style={{ color }}>·</span>
                                  {s}
                                </li>
                              ))
                            : <li className="text-sm text-dim">—</li>
                          }
                        </ul>
                      </div>
                    )
                  })}
                </motion.div>
              )}

              {/* Audit notes */}
              {verdict?.audit_notes && verdict.audit_notes.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.35 }}
                  className="bg-card border border-white/[0.07] rounded-2xl p-6"
                >
                  <p className="text-xs font-semibold text-muted tracking-widest uppercase mb-3">
                    Audit Notes
                  </p>
                  <ul className="flex flex-col gap-1.5">
                    {verdict.audit_notes.map((n, i) => (
                      <li key={i} className="text-sm text-muted leading-relaxed">{n}</li>
                    ))}
                  </ul>
                </motion.div>
              )}

              {/* CTAs */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.4 }}
                className="flex gap-3 justify-center pt-2"
              >
                <motion.button
                  whileHover={{ scale: 1.03, boxShadow: '0 0 20px 4px rgba(124,92,252,0.35)' }}
                  whileTap={{ scale: 0.97 }}
                  onClick={() => router.push('/debate/setup')}
                  className="bg-cta text-white font-semibold px-7 py-3 rounded-full text-sm"
                >
                  Start Another Debate
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.97 }}
                  onClick={() => router.push('/history')}
                  className="text-ink font-semibold px-7 py-3 rounded-full border border-white/[0.13] text-sm hover:border-white/20 transition-all"
                >
                  View History
                </motion.button>
              </motion.div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default function SummaryPage() {
  return (
    <Suspense>
      <SummaryPageInner />
    </Suspense>
  )
}
