'use client'
import { motion } from 'framer-motion'

interface VoiceIndicatorProps {
  active: boolean
  color?: string
  barCount?: number
}

export function VoiceIndicator({ active, color = '#e87848', barCount = 20 }: VoiceIndicatorProps) {
  const bars = Array.from({ length: barCount }, (_, i) => i)

  return (
    <div className="flex items-center gap-[3px] h-14" aria-label={active ? 'Recording' : 'Idle'}>
      {bars.map(i => (
        <motion.div
          key={i}
          style={{
            width: 3,
            borderRadius: 2,
            background: active ? color : '#3a3a58',
            transformOrigin: 'center',
          }}
          animate={
            active
              ? { scaleY: [0.25, 1, 0.25] }
              : { scaleY: 0.25 }
          }
          transition={
            active
              ? {
                  duration: 0.35 + (i % 5) * 0.12,
                  delay: (i * 0.045) % 0.45,
                  repeat: Infinity,
                  ease: 'easeInOut',
                }
              : { duration: 0.3 }
          }
          className="self-center min-h-[4px]"
        />
      ))}
    </div>
  )
}
