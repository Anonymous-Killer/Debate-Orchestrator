// lib/api.ts — centralized API service for Debate Orchestrator
// Backend: FastAPI at http://127.0.0.1:8000

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8000'
const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === 'true'

// ── Types ────────────────────────────────────────────────────────────────────

export interface LiveScore {
  side_a_percent: number
  side_b_percent: number
  delta_a?: number
  delta_b?: number
  trend: 'up' | 'down' | 'steady' | 'rising' | 'falling'
  confidence?: number
  reasoning_summary?: string
  is_provisional: boolean
  updated_at?: string
}

export interface DebateSession {
  id: string
  topic: string
  status: 'created' | 'active' | 'completed' | 'ended'
  current_phase: string
  capture_status: 'idle' | 'recording' | 'ended' | 'processing' | 'completed'
  participants: { a: string; b: string }
  stances: { a: string | null; b: string | null }
  active_side: 'A' | 'B'
  live_score: LiveScore
}

export interface Turn {
  id: string
  session_id: string
  speaker_side: 'A' | 'B'
  sequence_no: number
  transcript_text: string
  transcription_source?: string
  created_at: string
  metadata?: Record<string, unknown>
}

export interface UtteranceResponse {
  accepted: boolean
  session_id: string
  active_side: 'A' | 'B'
  capture_status: string
  sequence_no: number
  transcript_text: string
  transcription_source?: string
  live_score: LiveScore
}

export interface Verdict {
  id?: string
  session_id: string
  winner: 'A' | 'B'
  summary: string
  strengths: string[]
  weaknesses?: string[]
  deciding_factors?: string[]
  audit_notes?: string[]
  // normalised for UI use
  live_score?: LiveScore
  confidence?: number
  strengthsMap?: { a: string[]; b: string[] }
}

export interface DebateListItem {
  id: string
  topic: string
  participant_a_id: string
  participant_b_id: string
  winner?: 'A' | 'B'
  live_score?: LiveScore
  status?: string
}

export interface CreateDebateRequest {
  topic: string
  participant_a_id: string
  participant_b_id: string
  rules?: { scoring_style?: string; min_utterances_per_side?: number }
}

export interface StartDebateRequest {
  stance_a: string
  stance_b: string
  active_side?: 'A' | 'B'
}

// ── Real API Client ──────────────────────────────────────────────────────────

class RealAPIClient {
  private async req<T>(path: string, options: RequestInit = {}): Promise<T> {
    const res = await fetch(`${API_BASE}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({})) as { detail?: string }
      throw new Error(err.detail ?? `HTTP ${res.status}`)
    }
    const text = await res.text()
    return text ? (JSON.parse(text) as T) : ({} as T)
  }

  createDebate(body: CreateDebateRequest) {
    return this.req<DebateSession>('/debates', {
      method: 'POST',
      body: JSON.stringify(body),
    })
  }

  startDebate(id: string, body: StartDebateRequest) {
    return this.req<DebateSession>(`/debates/${id}/start`, {
      method: 'POST',
      body: JSON.stringify(body),
    })
  }

  submitUtterance(
    id: string,
    body: {
      transcript_text?: string
      audio_base64?: string
      audio_mime_type?: string
      audio_ref?: string
      idempotency_key?: string
    },
  ) {
    return this.req<UtteranceResponse>(`/debates/${id}/utterance`, {
      method: 'POST',
      body: JSON.stringify(body),
    })
  }

  switchSide(id: string, next_side: 'A' | 'B') {
    return this.req<DebateSession>(`/debates/${id}/switch-side`, {
      method: 'POST',
      body: JSON.stringify({ next_side }),
    })
  }

  endDebate(id: string) {
    return this.req<DebateSession>(`/debates/${id}/end`, { method: 'POST' })
  }

  getDebate(id: string) {
    return this.req<DebateSession>(`/debates/${id}`)
  }

  getLiveScore(id: string) {
    return this.req<LiveScore>(`/debates/${id}/live-score`)
  }

  getTranscript(id: string) {
    return this.req<{ session_id: string; turns: Turn[] }>(`/debates/${id}/transcript`)
  }

  getVerdict(id: string): Promise<Verdict> {
    return this.req<Verdict>(`/debates/${id}/verdict`, { method: 'POST' })
  }

  async listDebates(): Promise<DebateListItem[]> {
    const raw = await this.req<unknown[]>('/debates')
    return raw.map((d: any) => ({
      id: d.id,
      topic: d.topic,
      participant_a_id: d.participants?.a ?? d.participant_a_id ?? 'Side A',
      participant_b_id: d.participants?.b ?? d.participant_b_id ?? 'Side B',
      winner: d.winner,
      live_score: d.live_score,
      status: d.status,
    }))
  }
}

// ── Mock API Client ──────────────────────────────────────────────────────────

type MockStore = DebateSession & { _turns: Turn[] }
const _store: Record<string, MockStore> = {}

const delay = (ms = 600) => new Promise<void>(r => setTimeout(r, ms))
const uid = () => 'dbt-' + Math.random().toString(36).slice(2, 10)

class MockAPIClient {
  async createDebate(body: CreateDebateRequest): Promise<DebateSession> {
    await delay(500)
    const id = uid()
    const s: MockStore = {
      id,
      topic: body.topic,
      status: 'created',
      current_phase: 'INIT',
      capture_status: 'idle',
      participants: { a: body.participant_a_id, b: body.participant_b_id },
      stances: { a: null, b: null },
      active_side: 'A',
      live_score: { side_a_percent: 50, side_b_percent: 50, trend: 'steady', is_provisional: true },
      _turns: [],
    }
    _store[id] = s
    return s
  }

  async startDebate(id: string, body: StartDebateRequest): Promise<DebateSession> {
    await delay(400)
    const s = _store[id]
    if (!s) throw new Error('Debate not found')
    s.status = 'active'
    s.current_phase = 'LIVE_CAPTURE'
    s.capture_status = 'recording'
    s.stances = { a: body.stance_a, b: body.stance_b }
    s.active_side = body.active_side ?? 'A'
    return s
  }

  async submitUtterance(id: string, body: { transcript_text?: string }): Promise<UtteranceResponse> {
    await delay(800)
    const s = _store[id]
    if (!s) throw new Error('Debate not found')
    const side = s.active_side
    const drift = Math.floor(Math.random() * 14) - 5
    const newA = Math.min(85, Math.max(15, s.live_score.side_a_percent + (side === 'A' ? drift : -drift)))
    s.live_score = {
      side_a_percent: newA,
      side_b_percent: 100 - newA,
      trend: drift > 0 ? 'up' : 'down',
      is_provisional: true,
    }
    const turn: Turn = {
      id: uid(),
      session_id: id,
      speaker_side: side,
      sequence_no: s._turns.length + 1,
      transcript_text: body.transcript_text ?? `[Voice turn ${s._turns.length + 1}]`,
      created_at: new Date().toISOString(),
    }
    s._turns.push(turn)
    return {
      accepted: true,
      session_id: id,
      active_side: side,
      capture_status: 'recording',
      sequence_no: turn.sequence_no,
      transcript_text: turn.transcript_text,
      live_score: s.live_score,
    }
  }

  async switchSide(id: string, next_side: 'A' | 'B'): Promise<DebateSession> {
    await delay(300)
    const s = _store[id]
    if (!s) throw new Error('Debate not found')
    s.active_side = next_side
    return s
  }

  async endDebate(id: string): Promise<DebateSession> {
    await delay(700)
    const s = _store[id]
    if (!s) throw new Error('Debate not found')
    s.status = 'completed'
    s.current_phase = 'AUDIT'
    s.capture_status = 'completed'
    return s
  }

  async getDebate(id: string): Promise<DebateSession> {
    await delay(300)
    const s = _store[id]
    if (!s) throw new Error('Debate not found')
    return s
  }

  async getLiveScore(id: string): Promise<LiveScore> {
    return _store[id]?.live_score ?? { side_a_percent: 50, side_b_percent: 50, trend: 'steady', is_provisional: true }
  }

  async getTranscript(id: string) {
    return { session_id: id, turns: _store[id]?._turns ?? [] }
  }

  async getVerdict(id: string): Promise<Verdict> {
    await delay(1200)
    const s = _store[id]
    const winner = (s?.live_score?.side_a_percent ?? 50) >= 50 ? 'A' as const : 'B' as const
    const nameA = s?.participants?.a ?? 'Side A'
    const nameB = s?.participants?.b ?? 'Side B'
    return {
      session_id: id,
      winner,
      summary: winner === 'A'
        ? `${nameA} presented a stronger, evidence-backed argument with clear logical structure and consistent stance.`
        : `${nameB} demonstrated superior reasoning and consistent rhetorical discipline throughout the debate.`,
      strengths: winner === 'A'
        ? ['Strong evidentiary support', 'Clear logical flow', 'Effective rebuttal technique']
        : ['Coherent counter-narrative', 'Effective cross-examination', 'Superior evidence quality'],
      weaknesses: ['Could strengthen rebuttals in the opening phase'],
      deciding_factors: ['Evidence quality', 'Logical consistency', 'Crowd momentum'],
      live_score: s?.live_score,
      confidence: 0.74,
      strengthsMap: {
        a: ['Strong evidentiary support', 'Clear logical flow'],
        b: ['Coherent counter-narrative', 'Effective cross-examination'],
      },
    }
  }

  async listDebates(): Promise<DebateListItem[]> {
    await delay(400)
    const sample: DebateListItem[] = [
      {
        id: 'sample-1',
        topic: 'Should AI replace human judges?',
        participant_a_id: 'Alex',
        participant_b_id: 'Jordan',
        winner: 'A',
        live_score: { side_a_percent: 63, side_b_percent: 37, trend: 'steady', is_provisional: false },
        status: 'completed',
      },
      {
        id: 'sample-2',
        topic: 'Is social media net positive for democracy?',
        participant_a_id: 'Morgan',
        participant_b_id: 'Riley',
        winner: 'B',
        live_score: { side_a_percent: 44, side_b_percent: 56, trend: 'steady', is_provisional: false },
        status: 'completed',
      },
    ]
    const stored = Object.values(_store)
      .filter(d => d.status === 'completed' || d.status === 'ended')
      .map(d => ({
        id: d.id,
        topic: d.topic,
        participant_a_id: d.participants.a,
        participant_b_id: d.participants.b,
        winner: (d.live_score.side_a_percent >= 50 ? 'A' : 'B') as 'A' | 'B',
        live_score: d.live_score,
        status: d.status,
      }))
    return [...stored, ...sample]
  }
}

// ── Export ───────────────────────────────────────────────────────────────────

export const api: RealAPIClient | MockAPIClient = USE_MOCK
  ? new MockAPIClient()
  : new RealAPIClient()
