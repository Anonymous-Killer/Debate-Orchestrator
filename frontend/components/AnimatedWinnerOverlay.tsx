'use client'
import { motion, AnimatePresence } from 'framer-motion'

interface AnimatedWinnerOverlayProps {
  phase: 'clash' | 'winner' | 'done'
  sideAName: string
  sideBName: string
  winnerName: string | null
  winnerColor: string
}

export function AnimatedWinnerOverlay({
  phase,
  sideAName,
  sideBName,
  winnerName,
  winnerColor,
}: AnimatedWinnerOverlayProps) {
  return (
    <AnimatePresence>
      {phase !== 'done' && (
        <motion.div
          key="overlay"
          initial={{ opacity: 1 }}
          exit={{ opacity: 0, transition: { duration: 0.9, ease: 'easeInOut' } }}
          className="fixed inset-0 z-50 bg-bg flex items-center justify-center overflow-hidden"
        >
          {/* Dynamic background glow */}
          <motion.div
            className="absolute inset-0 pointer-events-none"
            animate={{
              background:
                phase === 'winner'
                  ? `radial-gradient(circle at 50% 50%, ${winnerColor}44 0%, transparent 65%)`
                  : 'radial-gradient(circle at 50% 50%, rgba(15,15,27,0.6) 0%, transparent 70%)',
            }}
            transition={{ duration: 1.2 }}
          />

          {/* Ambient particles */}
          {phase === 'winner' && (
            <div className="absolute inset-0 pointer-events-none overflow-hidden">
              {Array.from({ length: 12 }, (_, i) => (
                <motion.div
                  key={i}
                  className="absolute w-1 h-1 rounded-full"
                  style={{ background: winnerColor, left: `${8 + i * 7.5}%`, top: '100%' }}
                  animate={{ y: '-110vh', opacity: [0, 1, 0] }}
                  transition={{ duration: 2 + (i % 3), delay: i * 0.1, repeat: Infinity }}
                />
              ))}
            </div>
          )}

          <AnimatePresence mode="wait">
            {phase === 'clash' && (
              <motion.div
                key="clash"
                className="flex items-center gap-10 z-10 w-full justify-center px-8"
                exit={{ opacity: 0, scale: 0.9, transition: { duration: 0.35 } }}
              >
                <motion.div
                  initial={{ x: -140, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ duration: 0.65, ease: [0.22, 1, 0.36, 1] }}
                  className="flex flex-col items-center gap-3"
                >
                  <span
                    className="font-display font-extrabold text-side-a"
                    style={{ fontSize: 'clamp(2.5rem,9vw,5.5rem)', letterSpacing: '-0.04em' }}
                  >
                    {sideAName}
                  </span>
                  <motion.div
                    className="h-1 rounded-full bg-side-a"
                    initial={{ width: 0 }}
                    animate={{ width: 72 }}
                    transition={{ delay: 0.3, duration: 0.4 }}
                  />
                </motion.div>

                <motion.span
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{ duration: 0.9, repeat: Infinity }}
                  className="font-display font-extrabold text-muted"
                  style={{ fontSize: 'clamp(1.2rem,3vw,2.2rem)' }}
                >
                  VS
                </motion.span>

                <motion.div
                  initial={{ x: 140, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ duration: 0.65, ease: [0.22, 1, 0.36, 1] }}
                  className="flex flex-col items-center gap-3"
                >
                  <span
                    className="font-display font-extrabold text-side-b"
                    style={{ fontSize: 'clamp(2.5rem,9vw,5.5rem)', letterSpacing: '-0.04em' }}
                  >
                    {sideBName}
                  </span>
                  <motion.div
                    className="h-1 rounded-full bg-side-b"
                    initial={{ width: 0 }}
                    animate={{ width: 72 }}
                    transition={{ delay: 0.3, duration: 0.4 }}
                  />
                </motion.div>
              </motion.div>
            )}

            {phase === 'winner' && winnerName && (
              <motion.div
                key="winner"
                initial={{ scale: 0.55, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ type: 'spring', stiffness: 280, damping: 20 }}
                className="text-center z-10 px-8"
              >
                <motion.p
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 }}
                  className="text-sm font-semibold tracking-widest uppercase mb-4"
                  style={{ color: winnerColor }}
                >
                  Winner
                </motion.p>
                <h1
                  className="font-display font-extrabold leading-none"
                  style={{
                    fontSize: 'clamp(3.5rem,13vw,8.5rem)',
                    color: winnerColor,
                    letterSpacing: '-0.04em',
                    textShadow: `0 0 80px ${winnerColor}88`,
                  }}
                >
                  {winnerName}
                </h1>
                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.4 }}
                  className="mt-6 text-muted text-base"
                >
                  Preparing verdict…
                </motion.p>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
