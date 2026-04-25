// Re-export all API types and add UI-specific types

export type {
  LiveScore,
  DebateSession,
  Turn,
  UtteranceResponse,
  Verdict,
  DebateListItem,
  CreateDebateRequest,
  StartDebateRequest,
} from '@/lib/api'

export type DebatePhase =
  | 'ready'
  | 'recording'
  | 'processing'
  | 'switching'
  | 'ended'

export type AnimPhase = 'clash' | 'winner' | 'done'

export interface UITurn {
  side: 'A' | 'B'
  name: string
  text: string
  seqNo: number
}
