"""
Script Generation Module
Uses the Anthropic API (Claude) to produce structured video scripts.
"""

import logging
import os
import re
from dataclasses import dataclass, field

import anthropic

from topic_selection.engine import Topic

log = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")


@dataclass
class ScriptSegment:
    label: str       # e.g. "hook", "intro", "section_1", "cta"
    content: str


@dataclass
class Script:
    topic_title: str
    segments: list[ScriptSegment] = field(default_factory=list)

    @property
    def full_text(self) -> str:
        return "\n\n".join(
            f"[{seg.label.upper()}]\n{seg.content}" for seg in self.segments
        )

    @property
    def word_count(self) -> int:
        return len(self.full_text.split())


SYSTEM_PROMPT = """\
You are an expert YouTube script writer.
Your scripts are engaging, educational, and optimised for audience retention.

Rules:
- Write in a conversational, direct tone — no filler phrases.
- Structure every script with clearly labelled segments: HOOK, INTRO, MAIN_CONTENT (split into 2–4 sections), and CTA.
- Each segment label must appear on its own line in the format: [SEGMENT_NAME]
- Hook must be under 30 seconds when spoken (~75 words). Create curiosity or tension immediately.
- Avoid clickbait — every promise in the hook must be fulfilled in the script.
- End with a clear, single call-to-action.
- Return ONLY the script — no preamble, no commentary.
"""


class ScriptGenerator:
    """
    Generates a structured video script for a given Topic using Claude.
    """

    MODEL = "claude-opus-4-5"
    MAX_TOKENS = 2000

    def __init__(self, api_key: str = ANTHROPIC_API_KEY):
        self.client = anthropic.Anthropic(api_key=api_key) if api_key else None

    async def generate(self, topic: Topic) -> Script:
        if not self.client:
            log.warning("No ANTHROPIC_API_KEY — returning stub script.")
            return self._stub_script(topic)

        prompt = self._build_prompt(topic)
        log.info("Calling Claude to generate script for '%s'…", topic.title)

        message = self.client.messages.create(
            model=self.MODEL,
            max_tokens=self.MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        raw_text = message.content[0].text
        segments = self._parse_segments(raw_text)

        script = Script(topic_title=topic.title, segments=segments)
        log.info(
            "Script generated: %d segments, %d words.", len(segments), script.word_count
        )
        return script

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_prompt(self, topic: Topic) -> str:
        return (
            f"Write a YouTube video script about: {topic.title}\n\n"
            f"Context: This is a {topic.tags[0] if topic.tags else 'general'} channel.\n"
            f"Keyword to target: {topic.keyword}\n\n"
            f"Make it engaging, informative, and around 800–1000 words total."
        )

    @staticmethod
    def _parse_segments(raw: str) -> list[ScriptSegment]:
        """
        Splits raw Claude output into labelled segments.
        Expects lines like:  [HOOK]  or  [MAIN_CONTENT_1]
        """
        pattern = re.compile(r"^\[([A-Z_0-9]+)\]", re.MULTILINE)
        parts = pattern.split(raw.strip())

        # parts = ["", "HOOK", "hook text…", "INTRO", "intro text…", …]
        segments = []
        if len(parts) < 3:
            # Fallback: treat whole text as a single segment
            return [ScriptSegment(label="full_script", content=raw.strip())]

        it = iter(parts[1:])   # skip leading empty string
        for label, content in zip(it, it):
            segments.append(ScriptSegment(label=label.lower(), content=content.strip()))

        return segments

    @staticmethod
    def _stub_script(topic: Topic) -> Script:
        return Script(
            topic_title=topic.title,
            segments=[
                ScriptSegment("hook", f"Did you know {topic.title} is changing everything?"),
                ScriptSegment("intro", f"In this video, we'll explore {topic.title} in depth."),
                ScriptSegment("main_content_1", "This is where the main content goes."),
                ScriptSegment("cta", "Like and subscribe for more content like this."),
            ],
        )
