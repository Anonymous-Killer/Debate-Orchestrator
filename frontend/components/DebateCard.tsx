'use client'
import { motion } from 'framer-motion'
import { useRouter } from 'next/navigation'
import type { DebateListItem } from '@/lib/api'

interface DebateCardProps {
  debate: DebateListItem
  index: number
}

export function DebateCard({ debate, index }: DebateCardProps) {
  const router = useRouter()
  const isWinnerA = debate.winner === 'A'
  const isWinnerB = debate.winner === 'B'
  const scoreA = debate.live_score?.side_a_percent ?? 50
  const scoreB = debate.live_score?.side_b_percent ?? 50
  const hasWinner = debate.winner != null

  function handleClick() {
    const params = new URLSearchParams({
      a: debate.participant_a_id,
      b: debate.participant_b_id,
    })
    router.push(`/debate/summary/${debate.id}?${params}`)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.07, duration: 0.4 }}
      whileHover={{ y: -2, boxShadow: '0 8px 40px rgba(0,0,0,0.45)' }}
      onClick={handleClick}
      role="button"
      tabIndex={0}
      onKeyDown={e => e.key === 'Enter' && handleClick()}
      className="grid gap-4 bg-card border border-white/[0.07] rounded-2xl p-5 cursor-pointer transition-colors hover:bg-card-hover hover:border-white/[0.13] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cta/50"
      style={{ gridTemplateColumns: '1fr auto 1fr' }}
    >
      {/* Side A */}
      <div className="flex flex-col gap-1.5 min-w-0">
        <span className="text-xs font-semibold text-side-a tracking-widest uppercase">Side A</span>
        <span
          className="font-display font-bold text-ink truncate"
          style={{ fontSize: isWinnerA ? '1.25rem' : '1rem' }}
        >
          {debate.participant_a_id}
        </span>
        {hasWinner && (
          isWinnerA ? (
            <span
              className="text-xs font-semibold px-2 py-0.5 rounded-full w-fit whitespace-nowrap"
              style={{ background: 'rgba(232,120,72,0.15)', color: '#e87848' }}
            >
              Winner · {scoreA}%
            </span>
          ) : (
            <span className="text-xs text-muted">{scoreA}%</span>
          )
        )}
      </div>

      {/* Center */}
      <div className="text-center flex flex-col gap-2 min-w-[160px] max-w-[220px]">
        <span className="text-xs font-semibold text-muted tracking-widest uppercase">Topic</span>
        <span className="text-sm text-ink italic leading-snug line-clamp-2">"{debate.topic}"</span>
        <div className="flex h-1 rounded-full overflow-hidden bg-white/[0.05] mt-1">
          <div
            style={{ width: `${scoreA}%`, background: '#e87848', transition: 'width 0.7s ease' }}
          />
          <div style={{ flex: 1, background: '#48a8e0' }} />
        </div>
        {debate.status && (
          <span className="text-xs text-dim capitalize">{debate.status}</span>
        )}
      </div>

      {/* Side B */}
      <div className="flex flex-col gap-1.5 items-end min-w-0">
        <span className="text-xs font-semibold text-side-b tracking-widest uppercase">Side B</span>
        <span
          className="font-display font-bold text-ink truncate"
          style={{ fontSize: isWinnerB ? '1.25rem' : '1rem' }}
        >
          {debate.participant_b_id}
        </span>
        {hasWinner && (
          isWinnerB ? (
            <span
              className="text-xs font-semibold px-2 py-0.5 rounded-full w-fit whitespace-nowrap"
              style={{ background: 'rgba(72,168,224,0.15)', color: '#48a8e0' }}
            >
              Winner · {scoreB}%
            </span>
          ) : (
            <span className="text-xs text-muted">{scoreB}%</span>
          )
        )}
      </div>
    </motion.div>
  )
}
