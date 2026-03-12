# Adaptive AI Content Pipeline

An experimental, feedback-driven system for automated video creation and performance-driven iteration.

```
Generate → Measure → Diagnose → Improve
```

---

## What it does

| Stage | Module | Description |
|---|---|---|
| 1 | Signal Discovery | Pulls trending keywords from Google Trends & YouTube |
| 2 | Topic Selection | Scores and ranks signals by niche relevance and novelty |
| 3 | Script Generation | Claude writes a structured, segmented video script |
| 4 | Quality Validation | Claude scores the script before production |
| 5 | Media Generation | Delegated to external tools (ComfyUI, TTS) — hookable |
| 6 | Publishing | Generates SEO-optimised title, description, tags, thumbnail brief |
| 7 | Analytics | Collects CTR, retention, engagement from YouTube Studio |
| 8 | Performance Diagnosis | Claude reasons about what to change next iteration |
| 9 | Strategy Adjustment | Insights feed back into topic selection and script generation |

---

## Quickstart

```bash
# 1. Clone the repo
git clone https://github.com/ydnas109-netizen/adaptive-ai-content-pipeline
cd adaptive-ai-content-pipeline

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 4. Run the pipeline
cd src
python pipeline.py
```

---

## Configuration

All settings live in `PipelineConfig` (or `.env`):

```python
PipelineConfig(
    niche="technology",           # Your channel niche
    max_topics_per_run=5,         # Candidates to evaluate
    min_quality_score=0.75,       # Scripts below this are rejected
    publish_enabled=False,        # Set True to enable upload
    analytics_lookback_days=30,   # How far back to pull analytics
    loop_iterations=1,            # Set >1 for continuous runs
)
```

---

## Project structure

```
src/
├── pipeline.py                        # Main orchestrator
├── signal_discovery/
│   └── trends.py                      # Google Trends + YouTube signals
├── topic_selection/
│   └── engine.py                      # Scoring and ranking
├── script_generation/
│   └── generator.py                   # Claude script writer
├── quality_validation/
│   └── validator.py                   # Claude quality auditor
├── publishing/
│   └── metadata.py                    # SEO metadata generator
├── analytics/
│   └── collector.py                   # YouTube Analytics API
└── performance_diagnosis/
    └── claude_reasoner.py             # Claude feedback loop brain
```

---

## Connecting real APIs

### Anthropic (required for AI features)
Set `ANTHROPIC_API_KEY` in `.env`.

### Google Trends (signal discovery)
```bash
pip install pytrends
```
Then uncomment the pytrends block in `signal_discovery/trends.py`.

### YouTube (analytics + publishing)
1. Create a project in [Google Cloud Console](https://console.cloud.google.com)
2. Enable **YouTube Data API v3** and **YouTube Analytics API v2**
3. Download OAuth2 credentials → `token.json`
4. Set `YOUTUBE_OAUTH_TOKEN_PATH=token.json` in `.env`

---

## Running tests

```bash
python tests/test_pipeline.py
```

All tests run without an API key using stubs and heuristic fallbacks.

---

## Status

Early prototype — core pipeline implemented, media generation stage is a hookable placeholder.

**Next priorities:**
- ComfyUI / TTS integration for media generation
- YouTube OAuth upload flow
- Web dashboard for monitoring runs and strategy memory

---

## License

MIT
