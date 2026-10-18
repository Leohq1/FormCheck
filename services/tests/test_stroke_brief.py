"""Stroke coaching stays general and still fits the public result."""

from formcheck.worker.stroke_brief import apply_stroke_brief, stroke_brief


class _Transport:
    def __init__(self, payload):
        self.payload = payload
        self.prompts: list[str] = []

    def complete(self, *, model: str, prompt: str, timeout_seconds: float):
        self.prompts.append(prompt)
        if isinstance(self.payload, Exception):
            raise self.payload
        return self.payload


def _gemini_card() -> dict:
    return {
        "summary": "Hit down steep, then hold your balance.",
        "tips": [
            {
                "phase": "Prepare",
                "title": "Set the racket early",
                "explanation": "Turn before the shuttle arrives. A late racket makes the smash flat.",
                "practice_cue": "Elbow leads the take-back.",
            },
            {
                "phase": "Strike",
                "title": "Snap down through it",
                "explanation": "Meet the shuttle high and in front. Send it steep past the net.",
                "practice_cue": "Contact in front of the shoulder.",
            },
            {
                "phase": "Recover",
                "title": "Stick the landing",
                "explanation": "Land on the front foot and pause. Be ready for the block.",
                "practice_cue": "Hold for one beat.",
            },
        ],
    }


def test_selected_stroke_reaches_the_prompt_and_the_cards():
    transport = _Transport(_gemini_card())
    brief = stroke_brief("smash", transport=transport)
    assert "smash" in transport.prompts[0]
    assert brief["summary"].startswith("Hit down")
    assert [tip["citations"][0]["locator"] for tip in brief["tips"]] == [
        "Prepare",
        "Strike",
        "Recover",
    ]
    assert brief["tips"][0]["finding_id"] == "smash"
    assert brief["limitations"] == []


def test_bad_model_output_uses_the_drop_fallback():
    brief = stroke_brief("drop", transport=_Transport(ValueError("unusable")))
    assert brief["model"] == "template-fallback"
    assert brief["tips"][1]["title"] == "Slow the racket head"
    assert brief["tips"][0]["citations"][0]["source_id"] == "stroke-brief"


def test_completed_result_keeps_the_uploaded_stroke():
    result = {
        "status": "completed",
        "stroke": {"type": "drop"},
        "feedback": {"summary": "old"},
        "versions": {"generation": "none", "corpus": "none"},
    }
    updated = apply_stroke_brief(result, transport=_Transport(_gemini_card()))
    assert updated["stroke"]["type"] == "drop"
    assert updated["feedback"]["tips"]
    assert updated["versions"]["corpus"] == "stroke-brief"
    assert result["feedback"]["summary"] == "old"
