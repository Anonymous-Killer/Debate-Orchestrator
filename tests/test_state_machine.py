from app.core.enums import DebatePhase
from app.core.exceptions import InvalidStateTransition
from app.orchestrator.state_machine import DebateStateMachine


def test_state_machine_allows_live_capture_flow():
    machine = DebateStateMachine()
    machine.ensure_can_transition(DebatePhase.INIT, DebatePhase.TOPIC_LOCK)
    machine.ensure_can_transition(DebatePhase.TOPIC_LOCK, DebatePhase.STANCE_CAPTURE)
    machine.ensure_can_transition(DebatePhase.STANCE_CAPTURE, DebatePhase.LIVE_CAPTURE)


def test_state_machine_rejects_invalid_transition():
    machine = DebateStateMachine()
    try:
        machine.ensure_can_transition(DebatePhase.INIT, DebatePhase.LIVE_CAPTURE)
    except InvalidStateTransition:
        assert True
    else:
        assert False, "Expected invalid state transition to fail"

