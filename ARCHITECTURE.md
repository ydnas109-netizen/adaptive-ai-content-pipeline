# System Architecture

This project explores a feedback-driven AI content pipeline designed to automate the process of discovering, producing, evaluating, and improving video content.

Instead of generating content once, the system operates as a continuous learning loop.

Core principle:
Generate → Measure → Diagnose → Improve.

---

# High Level Pipeline

Internet Signals
      ↓
Topic Discovery
      ↓
Idea Validation
      ↓
Script Generation
      ↓
Audio Generation
      ↓
Avatar / Visual Rendering
      ↓
Video Assembly
      ↓
Publishing
      ↓
Analytics Collection
      ↓
Performance Diagnosis (Claude)
      ↓
Strategy Adjustment
      ↓
Next Content Iteration

---

# Module Overview

## 1. Signal Discovery Layer

Collects signals that indicate potential audience interest.

Sources may include:

• Google Trends  
• YouTube search suggestions  
• YouTube Studio analytics  
• Public discussion platforms  

Goal:
Identify topics that show rising attention within a niche.

---

## 2. Topic Selection Engine

The system filters discovered signals and proposes content ideas.

Each idea is evaluated for:

• relevance to the channel niche  
• novelty or trend momentum  
• search interest  

Selected ideas are passed to the content generation stage.

---

## 3. Script Generation

Claude generates structured scripts based on the selected topic.

The script generation stage focuses on:

• logical narrative flow  
• clear information density  
• strong hooks and pacing  

Scripts are structured in segments to support downstream processing.

---

## 4. Quality Validation Layer

Before production begins, scripts are analyzed to prevent low-quality AI output.

Validation checks include:

• logical consistency  
• clarity of explanation  
• narrative progression  
• redundancy detection  

The goal is to avoid low-value “AI slop”.

---

## 5. Media Generation Pipeline

The validated script is transformed into media components.

Steps include:

• voice synthesis for narration  
• avatar rendering using tools such as ComfyUI  
• visual generation and scene composition  

Outputs are combined into structured video segments.

---

## 6. Video Assembly System

Segments are stitched together automatically.

This stage handles:

• synchronization of audio and visuals  
• transitions and timing  
• final video rendering  

Crash detection and automatic recovery are included to ensure long render jobs complete successfully.

---

## 7. Publishing Layer

The system prepares the video for distribution.

This includes:

• metadata generation  
• title and description creation  
• thumbnail strategy suggestions  

Content is then uploaded to the target platform.

---

## 8. Analytics Collection

After publishing, performance data is collected from analytics sources such as:

• YouTube Studio  
• engagement metrics  
• retention curves  
• click-through rate  

These signals represent the real-world performance of the content.

---

## 9. Performance Diagnosis (Claude Reasoning Layer)

Claude acts as the reasoning engine that interprets performance signals.

The system attempts to detect causes of growth stagnation such as:

• poor audience retention  
• weak title or thumbnail performance  
• topic saturation  
• pacing issues in the script

Claude analyzes these signals and proposes strategic adjustments.

---

## 10. Iterative Improvement Loop

Insights from the analytics stage are fed back into the topic discovery and generation layers.

Future content is adjusted based on:

• performance diagnostics  
• audience behavior patterns  
• topic engagement signals

This creates a continuous learning loop where the system evolves its content strategy over time.

---

# Long-Term Goal

The long-term goal of the project is to create an open-source toolkit that allows developers and creators to experiment with automated, feedback-driven content pipelines.

Rather than simply generating content, the system aims to explore how AI can participate in iterative creative processes that learn from real-world performance data.
