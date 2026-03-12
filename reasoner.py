"""
Performance Diagnosis — Claude Reasoning Layer
Interprets analytics signals and proposes actionable strategy adjustments.
"""

import logging
import os
import json
import re
from dataclasses import dataclass, field

import anthropic

from topic_selection.engine import Topic
from script_generation.generator import Script

log = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")


@dataclass
class Diagnosis:
    summary: str
    root_causes: list[str] = field(default_factory=list)
    adjustments: list[dict] = field(default_factory=list)
    confidence: float = 0.5


DIAGNOSIS_SYSTEM = """\
You are an expert YouTube growth strategist and data analyst.

You will receive:
- The topic and keyword used for a video
- Post-publish analytics data
- Any previous strategy hints already in use

Your task: identify the most likely root causes of any underperformance and
propose concrete, actionable adjustments for the NEXT content iteration.

Guidelines:
- CTR < 4% → thumbnail or title problem
- avg_view_percentage < 30% → pacing, structure, or topic-depth mismatch
- avg_view_percentage > 60% → strong — double down on this format
- high impressions but low CTR → topic has demand but thumbnail fails to convert
- low impressions → topic not surfaced; try broader keyword or different angle

Respond ONLY with valid JSON (no markdown) in this exact structure:
{
  "summary": "<2-sentence plain-English diagnosis>",
  "root_causes": ["<cause 1>", "<cause 2>"],
  "adjustments": [
    {
      "type": "topic_strategy",
      "action": "<what to change>",
      "preferred_topics": ["<keyword hint>"],
      "keywords": ["<keyword hint>"]
    },
    {
      "type": "script_strategy",
      "action": "<what to change in the script>"
    },
    {
      "type": "thumbnail_strategy",
      "action": "<what to change about the thumbnail>"
    }
  ],
  "confidence": <float 0.0-1.0>
}

Include only adjustments that are directly supported by the data.
"""


class PerformanceDiagnoser:
    MODEL = "claude-opus-4-5"
    MAX_TOKENS = 1000

    def __init__(self, api_key: str = ANTHROPIC_API_KEY):
        self.client = anthropic.Anthropic(api_key=api_key) if api_key else None

    async def diagnose(
        self,
        topic: Topic,
        script: Script,
        analytics: dict,
        past_strategy: list[dict] | None = None,
    ) -> Diagnosis:
        if not self.client:
            return self._heuristic_diagnosis(analytics)

        prompt = self._build_prompt(topic, script, analytics, past_strategy or [])

        try:
            message = self.client.messages.create(
                model=self.MODEL,
                max_tokens=self.MAX_TOKENS,
                system=DIAGNOSIS_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
            )
            return self._parse(message.content[0].text)
        except Exception as exc:
            log.warning("Diagnosis API call failed (%s) — using heuristic.", exc)
            return self._heuristic_diagnosis(analytics)

    # ------------------------------------------------------------------

    def _build_prompt(
        self,
        topic: Topic,
        script: Script,
        analytics: dict,
        past_strategy: list[dict],
    ) -> str:
        lines = [
            f"Topic: {topic.title}",
            f"Keyword: {topic.keyword}",
            "",
            "Analytics:",
            json.dumps(analytics, indent=2),
        ]
        if past_strategy:
            lines += ["", "Previous strategy adjustments already applied:", json.dumps(past_strategy, indent=2)]
        return "\n".join(lines)

    def _parse(self, raw: str) -> Diagnosis:
        clean = re.sub(r"```(?:json)?|```", "", raw).strip()
        try:
            data = json.loads(clean)
            return Diagnosis(
                summary=data.get("summary", "No summary provided."),
                root_causes=data.get("root_causes", []),
                adjustments=data.get("adjustments", []),
                confidence=float(data.get("confidence", 0.5)),
            )
        except (json.JSONDecodeError, ValueError):
            log.warning("Could not parse diagnosis JSON.")
            return Diagnosis(summary="Diagnosis parsing failed — manual review needed.")

    # ------------------------------------------------------------------
    # Heuristic fallback
    # ------------------------------------------------------------------

    @staticmethod
    def _heuristic_diagnosis(analytics: dict) -> Diagnosis:
        causes = []
        adjustments = []

        ctr = analytics.get("ctr", 0.05)
        retention = analytics.get("avg_view_percentage", 40)

        if ctr < 0.04:
            causes.append("Low click-through rate — title or thumbnail underperforming.")
            adjustments.append({
                "type": "thumbnail_strategy",
                "action": "Test a higher-contrast thumbnail with a clear focal point and bold text.",
            })

        if retention < 30:
            causes.append("Poor audience retention — pacing or content depth may be off.")
            adjustments.append({
                "type": "script_strategy",
                "action": "Shorten intro, add a pattern interrupt at the 30s mark, increase pacing.",
            })

        if retention > 60:
            causes.append("High retention — format is resonating well.")
            adjustments.append({
                "type": "topic_strategy",
                "action": "Continue with similar format and depth.",
                "preferred_topics": [],
                "keywords": [],
            })

        summary = (
            "Heuristic analysis complete. "
            + ("; ".join(causes) if causes else "No strong signals detected.")
        )

        return Diagnosis(
            summary=summary,
            root_causes=causes,
            adjustments=adjustments,
            confidence=0.4,
        )
