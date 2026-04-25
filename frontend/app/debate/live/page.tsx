'use client'
import { useState, useEffect, useRef, useCallback, Suspense } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useRouter, useSearchParams } from 'next/navigation'
import { api } from '@/lib/api'
import type { LiveScore } from '@/lib/api'
import type { DebatePhase, UITurn } from '@/types'
import { CrowdSplitBar } from '@/components/CrowdSplitBar'
import { VoiceIndicator } from '@/components/VoiceIndicator'
import { DynamicActionButton } from '@/components/DynamicActionButton'

function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onloadend = () => {
      const result = reader.result as string
      // strip the "data:audio/...;base64," prefix
      resolve(result.split(',')[1])
    }
    reader.onerror = reject
    reader.readAsDataURL(blob)
  })
}

function LivePageInner() {
  const router = useRouter()
  const params = useSearchParams()
  const id         = params.get('id') ?? ''
  const sideAName  = params.get('a') ?? 'Side A'
  const sideBName  = params.get('b') ?? 'Side B'
  const topic      = params.get('topic') ?? ''

  const [phase, setPhase]           = useState<DebatePhase>('ready')
  const [activeSide, setActiveSide] = useState<'A' | 'B'>('A')
  const [score, setScore]           = useState<LiveScore & { visible: boolean }>({
    side_a_percent: 50,
    side_b_percent: 50,
    trend: 'steady',
    is_provisional: true,
    visible: false,
  })
  const [turns, setTurns]     = useState<UITurn[]>([])
  const [status, setStatus]   = useState(`Ready — ${sideAName} goes first.`)
  const [error, setError]     = useState('')
  const [endLoading, setEndLoad] = useState(false)
  const [recSecs, setRecSecs] = useState(0)

  const timerRef      = useRef<ReturnType<typeof setInterval>>()
  const transcriptRef = useRef<HTMLDivElement>(null)
  const recorderRef   = useRef<MediaRecorder | null>(null)
  const chunksRef     = useRef<Blob[]>([])

  const sideName  = activeSide === 'A' ? sideAName : sideBName
  const sideColor = activeSide === 'A' ? '#e87848' : '#48a8e0'
  const nextSide: 'A' | 'B' = activeSide === 'A' ? 'B' : 'A'
  const nextName  = nextSide === 'A' ? sideAName : sideBName

  // Recording timer
  useEffect(() => {
    if (phase === 'recording') {
      setRecSecs(0)
      timerRef.current = setInterval(() => setRecSecs(s => s + 1), 1000)
    } else {
      clearInterval(timerRef.current)
    }
    return () => clearInterval(timerRef.current)
  }, [phase])

  // Auto-scroll transcript
  useEffect(() => {
    if (transcriptRef.current) {
      transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight
    }
  }, [turns])

  // Clean up recorder on unmount
  useEffect(() => {
    return () => {
      recorderRef.current?.stream?.getTracks().forEach(t => t.stop())
    }
  }, [])

  const handleMain = useCallback(async () => {
    // ── START RECORDING ──────────────────────────────────────────────
    if (phase === 'ready') {
      setError('')
      if (!navigator.mediaDevices?.getUserMedia) {
        setError('This browser does not support microphone recording.')
        return
      }
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
        const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
          ? 'audio/webm;codecs=opus'
          : MediaRecorder.isTypeSupported('audio/webm')
          ? 'audio/webm'
          : 'audio/ogg'
        const recorder = new MediaRecorder(stream, { mimeType })
        chunksRef.current = []
        recorder.ondataavailable = e => { if (e.data.size > 0) chunksRef.current.push(e.data) }
        recorder.start(200) // collect a chunk every 200 ms for smooth data flow
        recorderRef.current = recorder
        setPhase('recording')
        setStatus(`Recording ${sideName}… Press "End Point" when done.`)
      } catch (e) {
        const msg = (e as Error).message
        setError(
          msg.includes('Permission') || msg.includes('denied')
            ? 'Microphone access denied. Allow microphone in browser settings.'
            : `Could not start recording: ${msg}`,
        )
      }
      return
    }

    // ── STOP RECORDING & SUBMIT ──────────────────────────────────────
    if (phase === 'recording') {
      const recorder = recorderRef.current
      if (!recorder) return
      setPhase('processing')
      setStatus('Transcribing…')

      // Stop recorder; wait for final ondataavailable + onstop
      await new Promise<void>(resolve => {
        recorder.onstop = () => resolve()
        recorder.stop()
        recorder.stream.getTracks().forEach(t => t.stop())
      })

      setError('')
      try {
        const mimeType = recorder.mimeType || 'audio/webm'
        const blob = new Blob(chunksRef.current, { type: mimeType })
        const audio_base64 = await blobToBase64(blob)

        const result = await api.submitUtterance(id, {
          audio_base64,
          audio_mime_type: mimeType,
        })

        setScore({ ...result.live_score, visible: true })
        setTurns(t => [
          ...t,
          {
            side: activeSide,
            name: sideName,
            text: result.transcript_text,
            seqNo: result.sequence_no,
          },
        ])
        setPhase('switching')
        await api.switchSide(id, nextSide)
        setActiveSide(nextSide)
        setPhase('ready')
        setStatus(`${nextName}'s turn.`)
      } catch (e) {
        setError((e as Error).message)
        setPhase('ready')
      }
    }
  }, [phase, activeSide, sideName, nextSide, nextName, id])

  async function handleEnd() {
    if (endLoading) return
    setEndLoad(true)
    setError('')
    try {
      await api.endDebate(id)
      const params = new URLSearchParams({ a: sideAName, b: sideBName })
      router.push(`/debate/summary/${id}?${params}`)
    } catch (e) {
      setError((e as Error).message)
      setEndLoad(false)
    }
  }

  const fmtTime = (s: number) =>
    `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`

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
        <div className="flex-1 flex justify-center px-4">
          <span className="text-sm text-muted max-w-sm truncate italic">"{topic}"</span>
        </div>
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.97 }}
          onClick={handleEnd}
          disabled={endLoading || phase === 'processing' || phase === 'switching'}
          className="text-xs font-semibold px-4 py-1.5 rounded-full border transition-all disabled:opacity-40"
          style={{ color: '#e04848', borderColor: 'rgba(224,72,72,0.3)' }}
        >
          {endLoading ? 'Ending…' : 'End Debate'}
        </motion.button>
      </nav>

      <div className="max-w-4xl mx-auto px-6 py-8 flex flex-col gap-6">
        {/* Crowd split bar — hidden until first score */}
        <motion.div
          animate={{ opacity: score.visible ? 1 : 0, y: score.visible ? 0 : 20 }}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
          className="bg-card border border-white/[0.07] rounded-2xl p-5"
          style={{ pointerEvents: score.visible ? 'auto' : 'none' }}
        >
          <p className="text-xs font-semibold text-muted tracking-widest uppercase mb-3">
            Live Crowd Split
          </p>
          <CrowdSplitBar
            scoreA={score.side_a_percent}
            scoreB={score.side_b_percent}
            nameA={sideAName}
            nameB={sideBName}
          />
          {score.reasoning_summary && (
            <p className="text-xs text-dim mt-3 leading-relaxed">{score.reasoning_summary}</p>
          )}
        </motion.div>

        <div className="grid gap-6" style={{ gridTemplateColumns: '1fr 300px' }}>
          {/* Voice control panel */}
          <div className="bg-card border border-white/[0.07] rounded-2xl p-10 flex flex-col items-center gap-6">
            {/* Active side indicator */}
            <div className="flex items-center gap-2.5">
              <motion.div
                className="w-2.5 h-2.5 rounded-full"
                style={{ background: sideColor }}
                animate={
                  phase === 'recording'
                    ? { scale: [1, 1.4, 1], opacity: [1, 0.5, 1] }
                    : { scale: 1, opacity: 1 }
                }
                transition={{ repeat: Infinity, duration: 1 }}
              />
              <span
                className="font-display font-bold text-2xl tracking-tight"
                style={{ color: sideColor }}
              >
                {sideName}
              </span>
            </div>

            {/* Voice waveform */}
            <VoiceIndicator active={phase === 'recording'} color={sideColor} />

            {/* Recording timer */}
            <AnimatePresence>
              {phase === 'recording' && (
                <motion.div
                  key="timer"
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                  className="font-display font-bold text-3xl tabular-nums"
                  style={{ color: sideColor }}
                >
                  {fmtTime(recSecs)}
                </motion.div>
              )}
            </AnimatePresence>

            {/* Main CTA */}
            <DynamicActionButton
              phase={phase}
              activeSide={activeSide}
              sideName={sideName}
              sideColor={sideColor}
              onClick={handleMain}
            />

            <p className="text-sm text-muted text-center">{status}</p>

            <AnimatePresence>
              {error && (
                <motion.p
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="text-sm text-red-400 text-center"
                >
                  {error}
                </motion.p>
              )}
            </AnimatePresence>

            {/* Side legend */}
            <div className="w-full flex justify-between text-xs text-muted border-t border-white/[0.06] pt-4">
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-side-a inline-block" />
                {sideAName}
              </span>
              <span className="flex items-center gap-1.5">
                {sideBName}
                <span className="w-2 h-2 rounded-full bg-side-b inline-block" />
              </span>
            </div>
          </div>

          {/* Transcript sidebar */}
          <div className="flex flex-col gap-3">
            <p className="text-xs font-semibold text-muted tracking-widest uppercase">
              Transcript ({turns.length})
            </p>
            <div
              ref={transcriptRef}
              className="flex flex-col gap-2 max-h-[28rem] overflow-y-auto pr-1"
            >
              {turns.length === 0 && (
                <p className="text-dim text-sm py-6 text-center">Turns will appear here.</p>
              )}
              {turns.map((t, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: 10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3 }}
                  className="rounded-xl p-3"
                  style={{
                    background:
                      t.side === 'A'
                        ? 'rgba(232,120,72,0.09)'
                        : 'rgba(72,168,224,0.09)',
                    border: `1px solid ${
                      t.side === 'A'
                        ? 'rgba(232,120,72,0.18)'
                        : 'rgba(72,168,224,0.18)'
                    }`,
                  }}
                >
                  <p
                    className="text-xs font-bold mb-1"
                    style={{ color: t.side === 'A' ? '#e87848' : '#48a8e0' }}
                  >
                    Turn {t.seqNo} · {t.name}
                  </p>
                  <p className="text-xs text-muted leading-relaxed">{t.text}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function LivePage() {
  return (
    <Suspense>
      <LivePageInner />
    </Suspense>
  )
}
