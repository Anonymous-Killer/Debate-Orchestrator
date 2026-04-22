# Debate Orchestrator

Backend-only debate orchestration service for a voice-first debate flow with:

- live utterance capture
- explicit side switching
- provisional live crowd-style score splits
- post-debate claim extraction, evidence review, scoring, and verdict generation

## Run

```bash
uvicorn app.main:app --reload
```

## Test

```bash
pytest
```

