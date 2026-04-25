'use client'
import { motion } from 'framer-motion'

interface CrowdSplitBarProps {
  scoreA: number
  scoreB: number
  nameA: string
  nameB: string
  size?: 'sm' | 'md' | 'lg'
}

export function CrowdSplitBar({ scoreA, scoreB, nameA, nameB, size = 'md' }: CrowdSplitBarProps) {
  const heights = { sm: 'h-5', md: 'h-8', lg: 'h-10' }
  const textSizes = { sm: 'text-xs', md: 'text-sm', lg: 'text-base' }

  return (
    <div>
      <div className={`flex justify-between mb-2 ${textSizes[size]} font-semibold`}>
        <span className="text-side-a">{nameA} — {scoreA}%</span>
        <span className="text-side-b">{scoreB}% — {nameB}</span>
      </div>
      <div className={`flex ${heights[size]} rounded-full overflow-hidden bg-surface`}>
        <motion.div
          className="flex items-center justify-center"
          style={{ background: 'linear-gradient(90deg, #e87848, #e87848cc)' }}
          initial={{ width: '50%' }}
          animate={{ width: `${scoreA}%` }}
          transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1] }}
        >
          {scoreA > 18 && (
            <span className={`${size === 'sm' ? 'text-[10px]' : 'text-xs'} font-bold text-white`}>
              {scoreA}%
            </span>
          )}
        </motion.div>
        <motion.div
          className="flex-1 flex items-center justify-center"
          style={{ background: 'linear-gradient(90deg, #48a8e0cc, #48a8e0)' }}
        >
          {scoreB > 18 && (
            <span className={`${size === 'sm' ? 'text-[10px]' : 'text-xs'} font-bold text-white`}>
              {scoreB}%
            </span>
          )}
        </motion.div>
      </div>
    </div>
  )
}
