"""Deterministic evaluation primitives.

These checks are intentionally explainable and do not pretend to prove truth.
The evidence-overlap check is a heuristic signal, not a factuality guarantee.
"""
from __future__ import annotations

import re
import time
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class Check:
    name: str
    score: float
    passed: bool
    detail: str
    severity: str = "info"


def _tokens(text: str) -> set[str]:
    return {t.lower() for t in re.findall(r"[a-zA-Z0-9_'-]+", text) if len(t) > 2}


def evaluate(
    *,
    question: str,
    answer: str,
    evidence: list[str] | None = None,
    expected_schema: dict[str, Any] | None = None,
    latency_ms: float | None = None,
    estimated_cost_usd: float | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    checks: list[Check] = []

    nonempty = bool(answer.strip())
    checks.append(Check("non_empty", 1.0 if nonempty else 0.0, nonempty,
                        "Answer contains text." if nonempty else "Answer is empty.", "error"))

    word_count = len(answer.split())
    length_ok = 1 <= word_count <= 2000
    checks.append(Check("length_sanity", 1.0 if length_ok else 0.4, length_ok,
                        f"Answer contains {word_count} words; expected 1–2000.", "warning"))

    if evidence:
        answer_terms = _tokens(answer)
        evidence_terms = _tokens(" ".join(evidence))
        overlap = len(answer_terms & evidence_terms) / max(1, len(answer_terms))
        # This is only a lexical support indicator; semantic verification needs a judge.
        checks.append(Check("evidence_overlap", round(min(1.0, overlap), 3), overlap >= 0.15,
                            f"{overlap:.0%} of answer terms overlap supplied evidence. "
                            "Lexical overlap is not proof of factual correctness.",
                            "warning" if overlap < 0.15 else "info"))
    else:
        checks.append(Check("evidence_available", 0.5, False,
                            "No evidence supplied; factual support was not assessed.", "warning"))

    schema_score = 1.0
    schema_detail = "No output schema requested."
    if expected_schema is not None:
        missing = [key for key in expected_schema if key not in _safe_json_object(answer)]
        schema_score = 1.0 if not missing else 0.0
        schema_detail = "All required top-level keys are present." if not missing else (
            "Missing required top-level keys: " + ", ".join(missing)
        )
    checks.append(Check("structure", schema_score, schema_score == 1.0, schema_detail,
                        "error" if schema_score == 0 else "info"))

    risky_phrases = ["ignore all safety", "reveal the system prompt", "steal credentials"]
    matched = [phrase for phrase in risky_phrases if phrase in answer.lower()]
    safe = not matched
    checks.append(Check("basic_risk_screen", 1.0 if safe else 0.0, safe,
                        "No configured risky phrase found." if safe else
                        "Matched configured risky phrase(s): " + ", ".join(matched),
                        "error" if not safe else "info"))

    if latency_ms is not None:
        latency_ok = latency_ms <= 10_000
        checks.append(Check("latency_budget", 1.0 if latency_ok else 0.5, latency_ok,
                            f"Reported latency: {latency_ms:.1f} ms (budget: 10000 ms).",
                            "warning" if not latency_ok else "info"))
    if estimated_cost_usd is not None:
        cost_ok = estimated_cost_usd <= 0.05
        checks.append(Check("cost_budget", 1.0 if cost_ok else 0.5, cost_ok,
                            f"Estimated cost: ${estimated_cost_usd:.6f} (budget: $0.05).",
                            "warning" if not cost_ok else "info"))

    score = round(sum(c.score for c in checks) / len(checks), 3)
    hard_fail = any(c.severity == "error" and not c.passed for c in checks)
    duration_ms = (time.perf_counter() - started) * 1000
    return {
        "question": question,
        "score": score,
        "passed": score >= 0.7 and not hard_fail,
        "checks": [asdict(c) for c in checks],
        "evaluation_duration_ms": round(duration_ms, 3),
        "limitations": [
            "Heuristic checks do not establish factual truth.",
            "Use domain-specific golden datasets and a calibrated judge for production evaluation.",
        ],
    }


def _safe_json_object(value: str) -> dict[str, Any]:
    import json
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}
