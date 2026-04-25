'use client'
import { motion } from 'framer-motion'
import type { DebatePhase } from '@/types'

interface DynamicActionButtonProps {
  phase: DebatePhase
  activeSide: 'A' | 'B'
  sideName: string
  sideColor: string
  onClick: () => void
  disabled?: boolean
}

export function DynamicActionButton({
  phase,
  activeSide,
  sideName,
  sideColor,
  onClick,
  disabled = false,
}: DynamicActionButtonProps) {
  const isRecording = phase === 'recording'
  const isProcessing = phase === 'processing' || phase === 'switching'

  const label = isProcessing
    ? 'Processing…'
    : isRecording
    ? 'End Point'
    : `Start the point — ${sideName}`

  const bg = isRecording ? '#e04848' : sideColor
  const glowColor = isRecording ? 'rgba(224,72,72,0.45)' : `${sideColor}77`

  return (
    <motion.button
      onClick={onClick}
      disabled={disabled || isProcessing}
      whileHover={
        !disabled && !isProcessing
          ? { scale: 1.04, boxShadow: `0 0 24px 6px ${glowColor}` }
          : {}
      }
      whileTap={{ scale: 0.96 }}
      animate={{ backgroundColor: bg }}
      transition={{ duration: 0.22 }}
      className="font-semibold text-white text-base rounded-full px-8 py-3.5 flex items-center justify-center gap-2.5 disabled:opacity-40 disabled:cursor-not-allowed transition-opacity"
      style={{
        minWidth: 260,
        background: bg,
        animation: isRecording ? 'glowPulse 1.5s ease infinite' : 'none',
      }}
    >
      {isProcessing && (
        <div className="w-4 h-4 rounded-full border-2 border-white/30 border-t-white animate-spin" />
      )}
      {!isProcessing && (
        <span className="text-sm opacity-80">{isRecording ? '⏹' : '▶'}</span>
      )}
      <span>{label}</span>
    </motion.button>
  )
}
