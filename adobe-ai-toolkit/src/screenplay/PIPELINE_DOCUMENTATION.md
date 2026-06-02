# Multi-Agent Video Automation Pipeline - Technical Documentation

## Overview

The Multi-Agent Pipeline coordinates two specialized agents to transform raw video transcription data into production-ready cinematic instruction sets:

- **Agent 1 (Technical Trimmer)**: Processes word timestamps and silence intervals to detect dead air and generate perfectly-timed subtitles
- **Agent 2 (Creative Director)**: Applies mood-based creative directives (zoom effects, music cues) to enhance production value

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Raw Transcript Data (word_timestamps, silence_intervals)       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  Input Validation │
                    │  (Pydantic v2)   │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                                         │
    ┌───▼──────────────┐              ┌────────────▼─────┐
    │ Agent 1:         │              │ Agent 2:          │
    │ Technical         │              │ Creative          │
    │ Trimmer          │              │ Director          │
    │                   │              │                   │
    │ • Dead Air Cut   │              │ • Zoom Effects    │
    │ • Subtitle Gen   │              │ • Music Cues      │
    └───┬──────────────┘              └────────┬──────────┘
        │                                      │
        │  TechnicalTimeline                   │  CreativeDecisions
        │  (CutDeadAir, GenerateSubtitle)      │  (ZoomPunchIn, BackgroundMusic)
        │                                      │
        └────────────────┬─────────────────────┘
                         │
                    ┌────▼───────┐
                    │  Merge &    │
                    │  Validate   │
                    └────┬───────┘
                         │
                    ┌────▼────────────────────────────┐
                    │  PipelineOutput                  │
                    │  • technical_timeline            │
                    │  • creative_decisions            │
                    │  • execution_metadata            │
                    └─────────────────────────────────┘
```

---

## Core Components

### 1. TechnicalTimeline (Agent 1)

**Model**: `TechnicalTimeline`

**Actions**:

#### CutDeadAir
```python
{
    "action": "CUT_DEAD_AIR",
    "timestamp_start": 5.0,    # float - start of silence in seconds
    "timestamp_end": 6.5       # float - end of silence in seconds
}
```

**Purpose**: Marks dead air zones (silence + filler words) for ripple deletion in Premiere Pro

#### GenerateSubtitle
```python
{
    "action": "GENERATE_SUBTITLE",
    "chunk_id": 0,             # int - sequential subtitle identifier
    "text": "Hello world",     # str - subtitle text (4 words max)
    "start_time": 0.0,         # float - subtitle start
    "end_time": 2.5            # float - subtitle end
}
```

**Purpose**: Creates word-perfect timed subtitles (short chunks for cinematic impact)

---

### 2. CreativeDecisions (Agent 2)

**Model**: `CreativeDecisions`

**Actions**:

#### APPLY_ZOOM_PUNCH_IN
```python
{
    "action": "APPLY_ZOOM_PUNCH_IN",
    "timestamp": 5.2,          # float - exact moment zoom begins
    "zoom_level": 1.15         # float - 1.0 = no zoom, 1.15 = 15% magnification
}
```

**Purpose**: Applies kinetic punch-in zoom at emotional peaks for visual dynamics

#### BACKGROUND_MUSIC_CUE
```python
{
    "action": "BACKGROUND_MUSIC_CUE",
    "track_style": "ambient_cinematic",  # str - music genre/mood
    "volume_envelope": [
        {"timestamp": 0.0, "volume_level": 0.0},
        {"timestamp": 2.0, "volume_level": 0.6},
        {"timestamp": 10.0, "volume_level": 0.4}
    ]
}
```

**Purpose**: Layers background music with dynamic volume automation

---

## Input Schema (TranscriptData)

```python
{
    "word_timestamps": [
        {
            "word": "Hello",
            "start": 0.0,
            "end": 0.5,
            "confidence": 0.98
        },
        # ... more words
    ],
    "silence_intervals": [
        [5.0, 6.0],    # (start, end) in seconds
        [8.0, 8.5]
    ],
    "video_duration": 30.0,  # Total video length in seconds
    "full_transcript": "Hello there..."  # Optional: complete text
}
```

### Validation Rules

- `word_timestamps`: Required, non-empty list of dicts with `word`, `start`, `end`
- `video_duration`: Required, must be > 0
- `silence_intervals`: Optional list of [start, end] tuples
- Timestamps must be non-negative and in ascending order

---

## Main Orchestration Function

### `run_video_automation_pipeline()` Signature

```python
def run_video_automation_pipeline(
    transcript_data: Dict[str, Any],
    mood: str,
    video_mode: str = "Business",
    intensity_multiplier: float = 1.0,
    enable_validation: bool = True
) -> Dict[str, Any]
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `transcript_data` | Dict | Required | Raw video metadata with word timestamps |
| `mood` | str | Required | Emotional tone: "inspiring", "dramatic", "calm", "energetic" |
| `video_mode` | str | "Business" | Style: "Business" (fast paced) or "Educational" (slower, more B-roll) |
| `intensity_multiplier` | float | 1.0 | Scale effects [0.5 - 2.0]: 1.0 = normal, 1.5 = 50% more intense |
| `enable_validation` | bool | True | Enable strict Pydantic validation (set False for lenient mode) |

### Return Value

```python
{
    "technical_timeline": {
        "timeline": [
            {"action": "CUT_DEAD_AIR", "timestamp_start": ..., "timestamp_end": ...},
            {"action": "GENERATE_SUBTITLE", "chunk_id": ..., "text": ..., ...}
        ]
    },
    "creative_decisions": {
        "creative_actions": [
            {"action": "APPLY_ZOOM_PUNCH_IN", "timestamp": ..., "zoom_level": ...},
            {"action": "BACKGROUND_MUSIC_CUE", "track_style": ..., "volume_envelope": ...}
        ],
        "mood": "inspiring",
        "video_mode": "Business"
    },
    "execution_metadata": {
        "total_actions_generated": 12,
        "technical_actions_count": 7,
        "creative_actions_count": 5,
        "dead_air_zones_removed": 3,
        "subtitles_generated": 4,
        "pipeline_status": "success",  # "success", "validation_failed", "error"
        "validation_errors": [],
        "warnings": []
    }
}
```

---

## Mood-Based Creative Presets

Each mood applies different creative parameters:

| Mood | Zoom Level | Music Style | Base Volume | Typical Use |
|------|-----------|-------------|------------|------------|
| `inspiring` | 1.15 | upbeat_cinematic | 0.6 | Motivational, success stories |
| `dramatic` | 1.25 | dramatic_tension | 0.7 | Product launches, intense moments |
| `calm` | 1.05 | ambient_peaceful | 0.4 | Educational, meditation, slow pace |
| `energetic` | 1.20 | upbeat_corporate | 0.65 | Training videos, quick tips |

**Intensity Multiplier Effect**: If `intensity_multiplier=1.5`, zoom levels increase by 50% and music volume scales up proportionally.

---

## Execution Flow (Stage-by-Stage)

### Stage 1: Input Validation
- Pydantic validates schema (if `enable_validation=True`)
- Returns error output if validation fails
- Falls back to lenient parsing if disabled

### Stage 2: Technical Timeline Generation
```
(Agent 1 Process)
1. Detect dead air zones from silence_intervals and filler words
2. Generate subtitles in 4-word chunks from word_timestamps
3. Combine and sort actions by timestamp
4. Return TechnicalTimeline model
```

### Stage 3: Creative Decisions
```
(Agent 2 Process)
1. Extract subtitle positions from technical timeline
2. Apply mood-based zoom effects at every 3rd subtitle
3. Build volume envelope (fade-in, sustain, fade-out)
4. Create background music cue with styling
5. Return CreativeDecisions model
```

### Stage 4: Compile Output
- Serialize both models to dicts
- Calculate execution statistics
- Build final PipelineOutput with metadata
- Return JSON-ready dictionary

---

## Error Handling & Validation

### Validation Strategy

```python
# Strict mode (default)
output = run_video_automation_pipeline(
    transcript_data=data,
    mood="inspiring",
    enable_validation=True  # Raises ValidationError on bad input
)

# Lenient mode
output = run_video_automation_pipeline(
    transcript_data=data,
    mood="inspiring",
    enable_validation=False  # Returns error_output dict instead
)
```

### Error Response Format

When pipeline fails, output contains:

```python
{
    "technical_timeline": {"timeline": []},
    "creative_decisions": {"creative_actions": [], "mood": "unknown", "video_mode": "Business"},
    "execution_metadata": {
        "pipeline_status": "validation_failed",  # or "error"
        "validation_errors": ["Missing required key: video_duration"],
        "warnings": [],
        ...
    }
}
```

### Common Validation Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Missing required key: video_duration` | No duration provided | Add `"video_duration": <duration_in_seconds>` |
| `Missing required key: word_timestamps` | No transcription data | Provide word-level timing array |
| `Expected type 'float', got 'str'` | Timestamp as string | Ensure all timestamps are numbers |
| `video_duration must be > 0` | Invalid duration | Provide positive number |

---

## Post-Execution Validation

### Validate Output

```python
from src.screenplay import validate_pipeline_output

output = run_video_automation_pipeline(data, "inspiring")
is_valid, errors = validate_pipeline_output(output)

if not is_valid:
    print(f"Validation failed: {errors}")
```

---

## Usage Examples

### Minimal Example

```python
transcript_data = {
    "word_timestamps": [
        {"word": "Hello", "start": 0.0, "end": 0.5},
        {"word": "world", "start": 0.5, "end": 1.0}
    ],
    "video_duration": 5.0
}

output = run_video_automation_pipeline(
    transcript_data=transcript_data,
    mood="inspiring"
)
```

### Full Example

```python
output = run_video_automation_pipeline(
    transcript_data={
        "word_timestamps": [...],
        "silence_intervals": [(5.0, 6.0)],
        "video_duration": 30.0,
        "full_transcript": "Complete transcript..."
    },
    mood="dramatic",
    video_mode="Business",
    intensity_multiplier=1.3,
    enable_validation=True
)

# Export to JSON
import json
json.dump(output, open("screenplay.json", "w"), indent=2)
```

---

## Integration with Adobe CEP Extension

### Payload Format for Premiere Pro

The pipeline output can be sent directly to Adobe CEP extension:

```javascript
// In PANELWIN.html
const screenplay = pipelineOutput.technical_timeline;
const creative = pipelineOutput.creative_decisions;

// Apply cuts
screenplay.timeline
    .filter(a => a.action === "CUT_DEAD_AIR")
    .forEach(cut => performRippleDelete(cut.timestamp_start, cut.timestamp_end));

// Apply subtitles
screenplay.timeline
    .filter(a => a.action === "GENERATE_SUBTITLE")
    .forEach(sub => applySubtitleBurnIn(sub.start_time, sub.end_time, sub.text));

// Apply creative effects
creative.creative_actions.forEach(action => {
    if (action.action === "APPLY_ZOOM_PUNCH_IN") {
        applyZoomEffect(action.timestamp, action.zoom_level);
    } else if (action.action === "BACKGROUND_MUSIC_CUE") {
        applyMusicBed(action.track_style, action.volume_envelope);
    }
});
```

---

## Performance Characteristics

| Operation | Typical Time |
|-----------|-------------|
| Input validation | <10ms |
| Agent 1 (dead air + subtitles) | 50-150ms |
| Agent 2 (creative decisions) | 30-80ms |
| Output serialization | <5ms |
| **Total Pipeline** | **100-250ms** |

---

## Type Hints & IDE Support

All functions include explicit type hints for IDE autocomplete:

```python
from src.screenplay import (
    run_video_automation_pipeline,
    validate_pipeline_output,
    PipelineOutput,
    TranscriptData,
    CreativeDecisions,
    TechnicalTimeline
)

# Full type inference
output: Dict[str, Any] = run_video_automation_pipeline(...)
is_valid: bool; errors: List[str] = validate_pipeline_output(output)
```

---

## Dependencies

- `pydantic >= 2.0`: Schema validation
- `typing`: Type hints
- `.technical_video_trimmer`: Agent 1 executor
- `.creative_director`: Agent 2 executor

---

## Related Files

- `technical_video_trimmer.py`: Agent 1 implementation
- `creative_director.py`: Agent 2 implementation
- `PIPELINE_EXAMPLES.py`: Usage examples
- `screenplay_architect.py`: Final JSON structure builder

