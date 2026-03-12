"""
Quality Validation Layer
Scores scripts before sending them to production to prevent low-value AI output.
"""

import logging
import os
import json
import re
from dataclasses import dataclass

import anthropic

from script_generation.generator import Script

log = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")


@dataclass
class ValidationResult:
    score: float          # 0.0 – 1.0
    passed: bool
    feedback: str
    details: dict


VALIDATOR_SYSTEM = """\
You are a strict video content quality auditor.

Evaluate the provided script on these criteria:
1. logical_consistency    – does the script make sense end-to-end? (0–10)
2. clarity                – are explanations clear and jargon-free where needed? (0–10)
3. narrative_progression  – does it build naturally from hook to CTA? (0–10)
4. redundancy             – is it free of repetitive or filler content? (0–10)
5. hook_strength          – does the hook create genuine curiosity? (0–10)

Respond ONLY with valid JSON (no markdown, no explanation) in this exact structure:
{
  "logical_consistency": <int>,
  "clarity": <int>,
  "narrative_progression": <int>,
  "redundancy": <int>,
  "hook_strength": <int>,
  "overall_feedback": "<one sentence summary of the main weakness>",
  "pass": <true|false>
}

Pass threshold: average score >= 7.0 and no single criterion below 5.
"""


class QualityValidator:
    """
    Uses Claude to evaluate script quality before production.
    Falls back to a heuristic check if no API key is available.
    """

    MODEL = "claude-haiku-4-5-20251001"   # fast + cheap for validation
    MAX_TOKENS = 400

    def __init__(self, min_score: float = 0.75, api_key: str = ANTHROPIC_API_KEY):
        self.min_score = min_score
        self.client = anthropic.Anthropic(api_key=api_key) if api_key else None

    async def validate(self, script: Script) -> ValidationResult:
        if not self.client:
            return self._heuristic_validate(script)

        try:
            message = self.client.messages.create(
                model=self.MODEL,
                max_tokens=self.MAX_TOKENS,
                system=VALIDATOR_SYSTEM,
                messages=[
                    {"role": "user", "content": f"Script to evaluate:\n\n{script.full_text}"}
                ],
            )
            return self._parse_response(message.content[0].text)

        except Exception as exc:
            log.warning("Quality validation API call failed (%s) — using heuristic.", exc)
            return self._heuristic_validate(script)

    # ------------------------------------------------------------------
    # Response parsing
    # ------------------------------------------------------------------

    def _parse_response(self, raw: str) -> ValidationResult:
        # Strip any accidental markdown fences
        clean = re.sub(r"```(?:json)?|```", "", raw).strip()

        try:
            data = json.loads(clean)
        except json.JSONDecodeError:
            log.warning("Could not parse validator JSON response; falling back.")
            return self._fallback_result()

        criteria_keys = [
            "logical_consistency", "clarity",
            "narrative_progression", "redundancy", "hook_strength"
        ]
        scores = [data.get(k, 5) for k in criteria_keys]
        avg = sum(scores) / len(scores)
        score_normalised = avg / 10.0

        passed = (
            score_normalised >= self.min_score
            and all(s >= 5 for s in scores)
        )

        return ValidationResult(
            score=round(score_normalised, 3),
            passed=passed,
            feedback=data.get("overall_feedback", ""),
            details={k: data.get(k) for k in criteria_keys},
        )

    # ------------------------------------------------------------------
    # Fallbacks
    # ------------------------------------------------------------------

    def _heuristic_validate(self, script: Script) -> ValidationResult:
        """Simple rule-based check when Claude is not available."""
        issues = []

        if script.word_count < 200:
            issues.append("Script is too short (< 200 words).")

        has_hook = any(s.label == "hook" for s in script.segments)
        has_cta = any(s.label == "cta" for s in script.segments)
        if not has_hook:
            issues.append("Missing HOOK segment.")
        if not has_cta:
            issues.append("Missing CTA segment.")

        # Rough redundancy check: count repeated sentences
        sentences = script.full_text.split(". ")
        unique_ratio = len(set(sentences)) / max(len(sentences), 1)
        if unique_ratio < 0.7:
            issues.append("High sentence repetition detected.")

        score = max(0.0, 1.0 - len(issues) * 0.2)
        return ValidationResult(
            score=round(score, 3),
            passed=score >= self.min_score,
            feedback="; ".join(issues) if issues else "Heuristic checks passed.",
            details={"heuristic": True, "issues": issues},
        )

    def _fallback_result(self) -> ValidationResult:
        return ValidationResult(
            score=0.5,
            passed=False,
            feedback="Validation inconclusive — manual review recommended.",
            details={},
        )
