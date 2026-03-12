"""
Test suite for the Adaptive AI Content Pipeline.
Runs all stages with stubs (no API key required).
"""

import asyncio
import sys
import os

# Make src importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

from signal_discovery.trends import SignalDiscovery, Signal
from topic_selection.engine import TopicSelectionEngine, Topic
from script_generation.generator import ScriptGenerator, Script, ScriptSegment
from quality_validation.validator import QualityValidator
from publishing.metadata import MetadataGenerator
from analytics.collector import AnalyticsCollector
from performance_diagnosis.claude_reasoner import PerformanceDiagnoser


# ── helpers ───────────────────────────────────────────────────────────

def ok(label: str):
    print(f"  ✓  {label}")

def fail(label: str, err):
    print(f"  ✗  {label}: {err}")
    raise SystemExit(1)


# ── tests ─────────────────────────────────────────────────────────────

async def test_signal_discovery():
    print("\n[1] Signal Discovery")
    sd = SignalDiscovery(niche="technology")
    signals = await sd.fetch()
    assert len(signals) > 0, "No signals returned"
    assert all(isinstance(s, Signal) for s in signals)
    ok(f"Fetched {len(signals)} signals")


async def test_topic_selection():
    print("\n[2] Topic Selection")
    signals = [
        Signal(keyword="AI automation tools", source="google_trends", trend_score=88),
        Signal(keyword="python for beginners", source="youtube_suggest", trend_score=72),
    ]
    engine = TopicSelectionEngine(niche="technology")
    topic = await engine.select(signals)
    assert isinstance(topic, Topic)
    assert topic.title
    assert 0 <= topic.score <= 1
    ok(f"Selected: '{topic.title}' (score={topic.score})")


async def test_script_generation():
    print("\n[3] Script Generation (stub — no API key)")
    topic = Topic(title="AI Automation Tools", keyword="AI automation tools", score=0.8, source="test")
    gen = ScriptGenerator(api_key="")   # forces stub
    script = await gen.generate(topic)
    assert isinstance(script, Script)
    assert script.word_count > 0
    assert len(script.segments) >= 3
    ok(f"Script: {script.word_count} words, {len(script.segments)} segments")


async def test_quality_validation():
    print("\n[4] Quality Validation (heuristic fallback)")
    script = Script(
        topic_title="Test",
        segments=[
            ScriptSegment("hook", "This will change everything you know about AI."),
            ScriptSegment("intro", "In this video we cover AI automation tools in depth."),
            ScriptSegment("main_content_1", " ".join(["Automation reduces manual work."] * 40)),
            ScriptSegment("cta", "Subscribe for more."),
        ],
    )
    validator = QualityValidator(min_score=0.5, api_key="")
    result = await validator.validate(script)
    assert result.score >= 0
    ok(f"Score: {result.score}, Passed: {result.passed}, Feedback: {result.feedback}")


async def test_metadata_generation():
    print("\n[5] Metadata Generation (stub)")
    topic = Topic(title="AI Automation Tools", keyword="AI automation tools", score=0.8, source="test", tags=["technology"])
    script = Script(topic_title="AI Automation Tools", segments=[
        ScriptSegment("hook", "Automate everything."),
    ])
    gen = MetadataGenerator(api_key="")
    meta = await gen.build(topic, script)
    assert meta.title
    assert meta.description
    ok(f"Title: {meta.title}")


async def test_analytics_collector():
    print("\n[6] Analytics Collection (simulated)")
    collector = AnalyticsCollector(lookback_days=30)
    data = await collector.collect("test_video_123")
    assert "views" in data
    assert "ctr" in data
    assert "retention_curve" in data
    ok(f"Views: {data['views']}, CTR: {data['ctr']}, Retention@50%: {data['retention_curve']['50%']}%")


async def test_performance_diagnosis():
    print("\n[7] Performance Diagnosis (heuristic fallback)")
    topic = Topic(title="AI Automation Tools", keyword="AI automation", score=0.8, source="test")
    script = Script(topic_title="AI Automation Tools", segments=[])
    analytics = {
        "views": 1200,
        "ctr": 0.03,               # below 4% — should flag thumbnail
        "avg_view_percentage": 25, # below 30% — should flag retention
    }
    diagnoser = PerformanceDiagnoser(api_key="")
    diagnosis = await diagnoser.diagnose(topic, script, analytics)
    assert diagnosis.summary
    assert len(diagnosis.adjustments) > 0
    ok(f"Diagnosis: {diagnosis.summary[:80]}…")
    ok(f"Adjustments proposed: {len(diagnosis.adjustments)}")


# ── runner ────────────────────────────────────────────────────────────

async def main():
    print("=" * 55)
    print("  Adaptive AI Content Pipeline — Test Suite")
    print("=" * 55)

    await test_signal_discovery()
    await test_topic_selection()
    await test_script_generation()
    await test_quality_validation()
    await test_metadata_generation()
    await test_analytics_collector()
    await test_performance_diagnosis()

    print("\n" + "=" * 55)
    print("  All tests passed ✓")
    print("=" * 55)


if __name__ == "__main__":
    asyncio.run(main())
