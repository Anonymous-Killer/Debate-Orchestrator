from datetime import datetime

from app.services.reasoning import NvidiaNIMReasoningProvider


def test_reasoning_json_dump_serializes_datetime_values():
    payload = {
        "previous_live_score": {
            "side_a_percent": 50,
            "side_b_percent": 50,
            "updated_at": datetime(2026, 4, 26, 12, 30, 0),
        }
    }

    dumped = NvidiaNIMReasoningProvider._json_dump(payload)

    assert '"updated_at": "2026-04-26T12:30:00"' in dumped
