"""General coaching for the stroke selected at upload."""

from __future__ import annotations

from typing import Any

from formcheck_rag.gemini import (
    UrllibGeminiTransport,
    gemini_config_from_env,
    load_local_gemini_env,
    parse_gemini_json,
)

STROKE_NAMES = {
    "overhead_clear": "overhead clear",
    "smash": "smash",
    "drop": "overhead drop",
}
PHASES = ("Prepare", "Strike", "Recover")
BRIEF_SOURCE = "stroke-brief"
PROMPT_VERSION = "stroke-brief-1"

_FALLBACKS: dict[str, dict[str, Any]] = {
    "overhead_clear": {
        "summary": "Send the shuttle high and deep, then get ready for the next one.",
        "tips": [
            {
                "phase": "Prepare",
                "title": "Turn before you reach",
                "explanation": "Get side-on as the shuttle drops behind you. A late turn makes the arm do all the work.",
                "practice_cue": "Point your front shoulder at the sideline before the swing starts.",
            },
            {
                "phase": "Strike",
                "title": "Reach up, then through",
                "explanation": "Meet the shuttle high with a long arm. Keep the swing moving forward after contact so the shuttle goes deep.",
                "practice_cue": "Finish with your racket hand past your front hip.",
            },
            {
                "phase": "Recover",
                "title": "Land and reload",
                "explanation": "Come down on balance and find the middle of the court. The clear only works if you are set for the reply.",
                "practice_cue": "Split-step as soon as your feet are quiet.",
            },
        ],
    },
    "smash": {
        "summary": "Hit down steep and early, then hold your balance for the next shot.",
        "tips": [
            {
                "phase": "Prepare",
                "title": "Set the racket early",
                "explanation": "Turn side-on and lift the racket while the shuttle is still in front of you. A rushed take-back makes the smash flat.",
                "practice_cue": "Elbow leads, racket head stays up behind you.",
            },
            {
                "phase": "Strike",
                "title": "Throw the hand down",
                "explanation": "Reach high and snap down through the shuttle. Aim past the net and into the ground in front of your opponent.",
                "practice_cue": "Contact in front of the shoulder, not above your head.",
            },
            {
                "phase": "Recover",
                "title": "Stick the landing",
                "explanation": "A steep smash pulls you forward. Land on the front foot and stop so you can cover the block.",
                "practice_cue": "Hold for one beat before you chase the shuttle.",
            },
        ],
    },
    "drop": {
        "summary": "Take the same shape as a clear, then let the shuttle fall just over the net.",
        "tips": [
            {
                "phase": "Prepare",
                "title": "Hide the shot",
                "explanation": "Use the same turn and racket prep as your clear. If the swing looks different, the drop is easy to read.",
                "practice_cue": "Start every drop with your clearing stance.",
            },
            {
                "phase": "Strike",
                "title": "Slow the racket head",
                "explanation": "Reach high, then ease off. The shuttle should tumble close to the net instead of sailing deep.",
                "practice_cue": "Feel the strings brush, not punch.",
            },
            {
                "phase": "Recover",
                "title": "Step in with it",
                "explanation": "A good drop brings you forward. Move in as the shuttle falls so you are there for the lift.",
                "practice_cue": "First step is toward the net, not backward.",
            },
        ],
    },
}


def apply_stroke_brief(result: dict[str, Any], transport: Any | None = None) -> dict[str, Any]:
    """Replace placeholder feedback with general advice for the selected stroke."""
    if result.get("status") != "completed":
        return result
    stroke = str((result.get("stroke") or {}).get("type") or "overhead_clear")
    brief = stroke_brief(stroke, transport)
    updated = dict(result)
    updated["feedback"] = brief
    versions = dict(result.get("versions") or {})
    versions["generation"] = str(brief["model"])
    versions["corpus"] = BRIEF_SOURCE
    updated["versions"] = versions
    return updated


def stroke_brief(stroke: str, transport: Any | None = None) -> dict[str, Any]:
    name = STROKE_NAMES.get(stroke, STROKE_NAMES["overhead_clear"])
    stroke_id = stroke if stroke in STROKE_NAMES else "overhead_clear"
    generated = _from_gemini(name, transport)
    payload = generated if generated is not None else _FALLBACKS[stroke_id]
    model = payload.get("model") or "template-fallback"
    tips = [_tip(stroke_id, item) for item in payload["tips"][:3]]
    return {
        "summary": str(payload["summary"]).strip(),
        "tips": tips,
        "limitations": [],
        "model": str(model),
        "prompt_version": PROMPT_VERSION,
    }


def _from_gemini(stroke_name: str, transport: Any | None) -> dict[str, Any] | None:
    load_local_gemini_env()
    config = gemini_config_from_env()
    if config is None and transport is None:
        return None
    client = transport
    model = config.model if config is not None else "gemini"
    timeout = config.timeout_seconds if config is not None else 20.0
    attempts = config.max_attempts if config is not None else 2
    if client is None and config is not None:
        client = UrllibGeminiTransport(config.api_key)
    if client is None:
        return None
    prompt = _prompt(stroke_name)
    for _attempt in range(max(1, attempts)):
        try:
            raw = client.complete(model=model, prompt=prompt, timeout_seconds=timeout)
            parsed = raw if "tips" in raw else parse_gemini_json(str(raw))
            checked = _checked(parsed)
            if checked is None:
                continue
            checked["model"] = model
            return checked
        except (ValueError, TimeoutError, OSError, TypeError, KeyError):
            continue
    return None


def _checked(payload: dict[str, Any]) -> dict[str, Any] | None:
    summary = payload.get("summary")
    tips = payload.get("tips")
    if not isinstance(summary, str) or not summary.strip():
        return None
    if not isinstance(tips, list) or len(tips) < 3:
        return None
    cleaned: list[dict[str, str]] = []
    for index, tip in enumerate(tips[:3]):
        if not isinstance(tip, dict):
            return None
        title = tip.get("title")
        explanation = tip.get("explanation")
        cue = tip.get("practice_cue")
        if not all(isinstance(item, str) and item.strip() for item in (title, explanation, cue)):
            return None
        phase = tip.get("phase")
        cleaned.append(
            {
                "phase": phase if isinstance(phase, str) and phase.strip() else PHASES[index],
                "title": title.strip(),
                "explanation": explanation.strip(),
                "practice_cue": cue.strip(),
            }
        )
    return {"summary": summary.strip(), "tips": cleaned}


def _tip(stroke_id: str, item: dict[str, str]) -> dict[str, Any]:
    return {
        "finding_id": stroke_id,
        "title": item["title"],
        "explanation": item["explanation"],
        "practice_cue": item["practice_cue"],
        "citations": [
            {
                "source_id": BRIEF_SOURCE,
                "chunk_id": stroke_id,
                "locator": item["phase"],
            }
        ],
    }


def _prompt(stroke_name: str) -> str:
    return (
        "You are a badminton coach writing a practice card for a recreational player. "
        f"The player selected this shot: {stroke_name}. "
        "You did not watch a video and you did not measure their body. "
        "Do not mention angles, scores, faults, or this specific clip. "
        "Write advice that is widely useful for that shot. "
        "Use short sentences. Do not use bullet characters or line breaks inside a field. "
        "Return JSON only, with a summary under 140 characters and exactly three tips "
        "in this order of phase: Prepare, Strike, Recover. "
        "Each tip has phase, title (3 to 6 words), explanation (two sentences), "
        "and practice_cue (one physical cue under 90 characters)."
    )


def _unused_import_guard() -> None:
    """Keep the generator import available for callers that swap transports."""
    _ = GeminiFeedbackGenerator
