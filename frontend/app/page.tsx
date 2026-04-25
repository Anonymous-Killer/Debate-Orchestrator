'use client'
import { motion } from 'framer-motion'
import { useRouter } from 'next/navigation'
import { useEffect, useRef } from 'react'

export default function LandingPage() {
  const router = useRouter()
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')!
    let animId: number
    let t = 0

    const orbs = [
      { x: 0.28, y: 0.45, r: 220, color: [232, 120, 72]  as [number, number, number], ox: 0.07, oy: 0.05 },
      { x: 0.72, y: 0.50, r: 220, color: [72,  168, 224] as [number, number, number], ox: -0.07, oy: -0.04 },
      { x: 0.50, y: 0.72, r: 130, color: [124, 92,  252] as [number, number, number], ox: 0.04, oy: 0.08 },
    ]

    function resize() {
      canvas!.width  = canvas!.offsetWidth
      canvas!.height = canvas!.offsetHeight
    }
    resize()
    window.addEventListener('resize', resize)

    function draw() {
      t++
      ctx.clearRect(0, 0, canvas!.width, canvas!.height)
      orbs.forEach(o => {
        const cx = (o.x + Math.sin(t * 0.008) * o.ox) * canvas!.width
        const cy = (o.y + Math.cos(t * 0.009) * o.oy) * canvas!.height
        const g = ctx.createRadialGradient(cx, cy, 0, cx, cy, o.r)
        g.addColorStop(0, `rgba(${o.color.join(',')},0.2)`)
        g.addColorStop(1, `rgba(${o.color.join(',')},0)`)
        ctx.fillStyle = g
        ctx.beginPath()
        ctx.arc(cx, cy, o.r, 0, Math.PI * 2)
        ctx.fill()
      })
      animId = requestAnimationFrame(draw)
    }
    draw()

    return () => {
      cancelAnimationFrame(animId)
      window.removeEventListener('resize', resize)
    }
  }, [])

  return (
    <div className="relative min-h-screen bg-bg overflow-hidden flex flex-col">
      <canvas ref={canvasRef} className="absolute inset-0 w-full h-full pointer-events-none" />

      {/* Nav */}
      <nav className="relative z-10 flex items-center px-8 py-4 border-b border-white/[0.07]">
        <span className="font-display font-bold text-xl tracking-tight">
          Debate<span className="text-cta">.</span>
        </span>
        <div className="flex-1" />
        <div className="flex items-center gap-2">
          <button
            onClick={() => router.push('/history')}
            className="text-sm font-medium text-muted hover:text-ink px-4 py-1.5 rounded-full border border-white/[0.07] hover:border-white/[0.14] transition-all"
          >
            History
          </button>
          <button
            onClick={() => router.push('/debate/setup')}
            className="text-sm font-semibold text-white bg-cta hover:opacity-90 px-4 py-1.5 rounded-full transition-all"
          >
            New Debate
          </button>
        </div>
      </nav>

      {/* Hero */}
      <div className="relative z-10 flex-1 flex flex-col items-center justify-center text-center px-6 py-20">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-6"
        >
          <span
            className="text-xs font-semibold px-3 py-1 rounded-full tracking-widest uppercase"
            style={{ background: 'rgba(124,92,252,0.15)', color: '#7c5cfc' }}
          >
            AI-Powered Debate Platform
          </span>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="font-display font-extrabold leading-[0.92] tracking-tight mb-6"
          style={{ fontSize: 'clamp(3rem,8vw,6rem)' }}
        >
          <span className="text-side-a">A</span>
          {' vs '}
          <span className="text-side-b">B</span>
          <br />
          <span className="text-ink">Let the best argument win.</span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="text-muted text-lg leading-relaxed max-w-md mb-12"
        >
          Voice-first debate orchestration with live crowd scoring and AI-generated verdicts.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="flex gap-3 flex-wrap justify-center"
        >
          <motion.button
            whileHover={{ scale: 1.04, boxShadow: '0 0 24px 6px rgba(124,92,252,0.4)' }}
            whileTap={{ scale: 0.97 }}
            onClick={() => router.push('/debate/setup')}
            className="bg-cta text-white font-semibold text-base px-8 py-3.5 rounded-full transition-all"
          >
            Create a Debate
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => router.push('/history')}
            className="text-ink font-semibold text-base px-8 py-3.5 rounded-full border border-white/[0.13] hover:border-white/20 transition-all"
          >
            View History
          </motion.button>
        </motion.div>

        {/* VS divider */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 0.5 }}
          transition={{ delay: 0.7 }}
          className="flex items-center gap-8 mt-20"
        >
          <div
            className="w-16 h-px"
            style={{ background: 'linear-gradient(to right, transparent, #e87848)' }}
          />
          <span className="font-display font-bold text-sm tracking-[0.18em] text-muted">VS</span>
          <div
            className="w-16 h-px"
            style={{ background: 'linear-gradient(to left, transparent, #48a8e0)' }}
          />
        </motion.div>

        {/* Feature pills */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.85 }}
          className="flex gap-6 mt-8 text-sm text-muted flex-wrap justify-center"
        >
          {[
            ['Voice-first capture', '#e87848'],
            ['Live crowd scoring', '#48a8e0'],
            ['AI verdict', '#7c5cfc'],
          ].map(([label, color]) => (
            <span key={label} className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full" style={{ background: color }} />
              <span>{label}</span>
            </span>
          ))}
        </motion.div>
      </div>
    </div>
  )
}
