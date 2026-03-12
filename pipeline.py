"""
Adaptive AI Content Pipeline
Main orchestration layer — runs the full Generate → Measure → Diagnose → Improve loop.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from signal_discovery.trends import SignalDiscovery
from topic_selection.engine import TopicSelectionEngine
from script_generation.generator import ScriptGenerator
from quality_validation.validator import QualityValidator
from publishing.metadata import MetadataGenerator
from analytics.collector import AnalyticsCollector
from performance_diagnosis.claude_reasoner import PerformanceDiagnoser

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
log = logging.getLogger("pipeline")


@dataclass
class PipelineConfig:
    niche: str = "technology"
    max_topics_per_run: int = 5
    min_quality_score: float = 0.75
    publish_enabled: bool = False          # flip to True when ready
    analytics_lookback_days: int = 30
    loop_iterations: int = 1               # set >1 for continuous runs


@dataclass
class PipelineResult:
    run_id: str
    topic: str
    script: Optional[str] = None
    quality_score: Optional[float] = None
    published: bool = False
    analytics: dict = field(default_factory=dict)
    diagnosis: Optional[str] = None
    strategy_adjustments: list = field(default_factory=list)
    errors: list = field(default_factory=list)


class AdaptiveContentPipeline:
    """
    Full feedback-driven content pipeline.

    Stages
    ------
    1. Signal Discovery     – find trending topics
    2. Topic Selection      – rank & filter by niche relevance
    3. Script Generation    – Claude writes a structured script
    4. Quality Validation   – score before production
    5. (Media generation)   – placeholder; handled externally / future modules
    6. Publishing           – metadata + upload prep
    7. Analytics Collection – pull real-world performance data
    8. Performance Diagnosis– Claude reasons about what to change
    9. Strategy Adjustment  – feed insights back into next iteration
    """

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.signal_discovery = SignalDiscovery(niche=config.niche)
        self.topic_engine = TopicSelectionEngine(niche=config.niche)
        self.script_generator = ScriptGenerator()
        self.quality_validator = QualityValidator(min_score=config.min_quality_score)
        self.metadata_generator = MetadataGenerator()
        self.analytics_collector = AnalyticsCollector(
            lookback_days=config.analytics_lookback_days
        )
        self.diagnoser = PerformanceDiagnoser()

        self._strategy_memory: list[dict] = []   # cross-iteration memory

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    async def run(self) -> list[PipelineResult]:
        results = []
        for iteration in range(self.config.loop_iterations):
            log.info("=== Pipeline iteration %d/%d ===", iteration + 1, self.config.loop_iterations)
            result = await self._run_iteration()
            results.append(result)

            if result.strategy_adjustments:
                self._apply_strategy_adjustments(result.strategy_adjustments)

        return results

    # ------------------------------------------------------------------
    # Single iteration
    # ------------------------------------------------------------------

    async def _run_iteration(self) -> PipelineResult:
        run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        result = PipelineResult(run_id=run_id, topic="unknown")

        try:
            # 1 — Signal Discovery
            log.info("[1/8] Discovering signals…")
            signals = await self.signal_discovery.fetch()
            log.info("  Found %d raw signals.", len(signals))

            # 2 — Topic Selection
            log.info("[2/8] Selecting best topic…")
            topic = await self.topic_engine.select(
                signals,
                strategy_hints=self._strategy_memory,
                max_candidates=self.config.max_topics_per_run,
            )
            result.topic = topic.title
            log.info("  Selected: '%s' (score=%.2f)", topic.title, topic.score)

            # 3 — Script Generation
            log.info("[3/8] Generating script…")
            script = await self.script_generator.generate(topic)
            result.script = script.full_text
            log.info("  Script length: %d words.", script.word_count)

            # 4 — Quality Validation
            log.info("[4/8] Validating script quality…")
            validation = await self.quality_validator.validate(script)
            result.quality_score = validation.score
            if not validation.passed:
                log.warning(
                    "  Quality check FAILED (score=%.2f). Skipping production.",
                    validation.score,
                )
                result.errors.append(f"Quality validation failed: {validation.feedback}")
                return result
            log.info("  Quality OK (score=%.2f).", validation.score)

            # 5 — Media Generation (external / future)
            log.info("[5/8] Media generation — delegated to external tools (ComfyUI, TTS…).")

            # 6 — Publishing prep
            log.info("[6/8] Generating publish metadata…")
            metadata = await self.metadata_generator.build(topic, script)
            log.info("  Title: %s", metadata.title)
            if self.config.publish_enabled:
                log.info("  Uploading…")
                # await publisher.upload(video_path, metadata)
                result.published = True
            else:
                log.info("  publish_enabled=False — skipping upload.")

            # 7 — Analytics Collection
            log.info("[7/8] Collecting analytics…")
            analytics = await self.analytics_collector.collect(video_id=run_id)
            result.analytics = analytics
            log.info("  Analytics: %s", analytics)

            # 8 — Performance Diagnosis
            log.info("[8/8] Running performance diagnosis…")
            diagnosis = await self.diagnoser.diagnose(
                topic=topic,
                script=script,
                analytics=analytics,
                past_strategy=self._strategy_memory,
            )
            result.diagnosis = diagnosis.summary
            result.strategy_adjustments = diagnosis.adjustments
            log.info("  Diagnosis complete. %d adjustments proposed.", len(diagnosis.adjustments))

        except Exception as exc:
            log.exception("Pipeline error: %s", exc)
            result.errors.append(str(exc))

        return result

    # ------------------------------------------------------------------
    # Strategy memory
    # ------------------------------------------------------------------

    def _apply_strategy_adjustments(self, adjustments: list[dict]) -> None:
        self._strategy_memory.extend(adjustments)
        # Keep only the most recent 20 insights to avoid context bloat
        self._strategy_memory = self._strategy_memory[-20:]
        log.info("Strategy memory updated (%d entries).", len(self._strategy_memory))


# ------------------------------------------------------------------
# CLI entry point
# ------------------------------------------------------------------

async def main():
    config = PipelineConfig(
        niche="technology",
        max_topics_per_run=5,
        min_quality_score=0.75,
        publish_enabled=False,
        analytics_lookback_days=30,
        loop_iterations=1,
    )

    pipeline = AdaptiveContentPipeline(config)
    results = await pipeline.run()

    print("\n=== Run Summary ===")
    for r in results:
        print(f"Run ID    : {r.run_id}")
        print(f"Topic     : {r.topic}")
        print(f"Quality   : {r.quality_score}")
        print(f"Published : {r.published}")
        print(f"Diagnosis : {r.diagnosis}")
        print(f"Errors    : {r.errors or 'none'}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
