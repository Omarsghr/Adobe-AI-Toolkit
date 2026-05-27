# AGENTS.md - Adobe AI Toolkit Codebase Guide

## Project Overview

**Adobe AI Toolkit** is a distributed video automation system that transforms raw video into production-ready Adobe Premiere Pro sequences. It's built as a **Client-Server pipeline** where:
- Backend (Python) handles transcription, audio analysis, and screenplay generation
- Frontend (Adobe CEP Extension) applies generated edits to Premiere Pro timelines
- GPU Services (Stable Diffusion API) generate visual assets

**Critical Mindset**: Think in terms of **5-step pipeline stages** with clear data flow between them.

---

## Architecture & Data Flow

### The 5-Stage Pipeline (see `main.py` and `master_glue.py`)

1. **Signal Analysis** (`src/signal_analysis/signal_processor.py`)
   - Detects silence zones in audio
   - Outputs to SQLite `silence_zones` table

2. **Transcription** (`src/transcription/transcription_manager.py`)
   - Whisper via Groq Cloud (15 API keys in .env for rate limiting)
   - **Extracts word-level timestamps** via `groq_clients.py::_extract_word_timestamps()`
   - Outputs full transcript + `map.json` (word timestamps)

3. **Audio Intelligence** (`src/screenplay/`)
   - `dead_air_detector.py`: Detects silence zones >0.5s + 15+ filler word patterns
   - `subtitle_generator.py`: Creates SRT/VTT with semantic word grouping
   - Outputs to SQLite `dead_air_zones` table

4. **Screenplay Generation** (`src/ai_logic/keyword_director.py`)
   - **Few-shot learning pattern**: Pulls `style_templates` from DB (set by user)
   - Generates image prompts + music beds with timing
   - Uses `ScreenplayArchitect` to format with mandatory 0.10s vocal padding
   - Outputs `adobe_screenplay.json` with multi-track timeline

5. **Visual Asset Generation** (`src/ai_logic/visualist_generator.py`)
   - Prompt optimization (keep <85 tokens for speed)
   - Calls Pollinations API or Stable Diffusion local API
   - Stores images in `assets/ai_images/`

**Data Dependency Chain**: File → Audio Extraction → Transcription (word timestamps) → Dead Air Detection → Screenplay Building → Image Generation → JSON Output

---

## Key Files & Patterns

### Server & Pipeline Orchestration
- **`server.py`**: FastAPI endpoints `/process-from-adobe` (standard) and `/process-with-analogy` (style-based)
  - Uses `PayloadFormatter` to validate & sanitize all outputs
  - Mandatory validation before sending to CEP panel
  
- **`main.py`**: Master orchestrator that chains sub-scripts with PYTHONPATH management
  - Accepts `target_audio` (file path) and `video_mode` ("Business", "Educational", etc.)
  - Exits on first failure (fail-fast)

- **`master_glue.py`**: Legacy 5-step subprocess runner

### Database Patterns (`project_memory.db`)

**Key Tables**:
- `transcript`: Full text + word timestamp array (JSON)
- `silence_zones`: Raw audio analysis output
- `dead_air_zones`: Silence + filler word detections
- `generated_assets`: Track cost estimates & prompt optimization
- `style_templates`: User-provided reference JSONs for few-shot learning

**Always initialize DB before queries**:
```python
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS ...")  # Idempotent
conn.commit()
conn.close()
```

### JSON Screenplay Format (`adobe_screenplay.json`)

Three-layer structure:
```json
{
  "project_configuration": {
    "target_sequence_fps": 30,
    "global_vocal_padding_seconds": 0.10,
    "default_image_cost_tier_usd": 0.004
  },
  "timeline_data": {
    "cuts_and_trims": [{"type": "dead_air_removal", "start_timestamp": 5.0, "end_timestamp": 7.5, "action_execution": "ripple_delete"}],
    "video_track_1_vocals": [{"padded_start_time": -0.1, "padded_end_time": 5.1, "subtitle_string": "...", "extracted_keywords": [...]}],
    "video_track_2_b_roll_images": [{"transition_behavior_in": "cross_dissolve", "transition_behavior_out": "fade", "generation_prompt": "..."}],
    "audio_track_1_vocals": [...],
    "audio_track_2_music_beds": [{"audio_ducking": {"active_while_vocals_playing": true, "attenuation_db": -12}, "fade_in_seconds": 2.0}]
  }
}
```

**Golden Rule**: Every vocal segment has **mandatory 0.10s padding** on both ends (prevents syllable clipping). This is enforced in `ScreenplayArchitect.add_vocal_segment()`.

### CEP Extension Pattern (`CEP/`)
- **`host.jsx`**: ExtendScript native Premiere Pro API calls
  - `applyScreenplayToTimeline()`: Entry point
  - `performRippleDelete()`: Delete with timeline shift
  - `applyTransition()`: Cross-dissolve, fade, etc.
  - `applyAudioDucking()`: Reduce music during speech
  - `applySubtitleBurnIn()`: Add subtitle track

- **`PANELWIN.html`**: 420×700 UI for file selection & status display
  - Sends to `/process-from-adobe` endpoint
  - Receives validated payload, calls `host.jsx` via `evalScript()`

---

## Critical Developer Conventions

### 1. **Path Handling** (Windows-First)
- All paths use forward slashes internally: `"C:/Users/dell/OneDrive/Desktop/.vscode/assets/..."`
- Never store backslash paths in JSON
- `PayloadFormatter.prepare_for_transmission()` handles conversion
- All output paths are **absolute** (no relative)

### 2. **API Key Management** (Rate Limiting)
```python
# .env file MUST have:
GROQ_API_KEY_1 through GROQ_API_KEY_15  # Rotated by groq_clients.py
```
Groq rotates keys on error to avoid rate limits. This is pattern you see in `groq_clients.py::transcribe_with_groq()`.

### 3. **Error Handling Pattern**
- **Fallback mechanisms**: If primary API fails, use secondary (e.g., Hugging Face → Replicate for music)
- **Graceful degradation**: Legacy screenplay format fallback in `keyword_director.py`
- **Validation before transmission**: All CEP payloads validated by `PayloadValidator`

### 4. **Module Organization**
Each major component is a package with clear responsibility:
- `src/transcription/`: Only audio → text
- `src/screenplay/`: JSON structure building (no API calls)
- `src/ai_logic/`: LLM-based generation
- `src/signal_analysis/`: Audio waveform processing
- `src/data_formatter/`: Cross-module utilities & validation

### 5. **Testing Pattern** (see `integration_test_suite.py`)
- Unit tests in integration_test_suite
- Sample payload generation for mock testing
- PayloadValidator catches 7+ error types
- Always verify paths exist before sending to CEP

---

## Common Developer Workflows

### Adding a New Audio Processing Stage
1. Create script in `src/screenplay/` or `src/signal_analysis/`
2. Accept `db_path` as parameter (never hardcode)
3. Read from appropriate table, write to new table
4. Insert step in `main.py` pipeline chain
5. Add fallback in `keyword_director.py`
6. Test with `integration_test_suite.py`

### Modifying Timeline JSON Structure
1. Update `ScreenplayArchitect` class (adds new track or field)
2. Update sample payload in `integration_test_suite.py`
3. Run validation tests
4. Update `PayloadValidator` if new fields are required
5. Update CEP `host.jsx` to handle new field

### Integrating New External API
1. Add key to `.env` file pattern documentation
2. Implement in corresponding `src/` module
3. Create fallback (required for production)
4. Add error handling with key rotation (if applicable)
5. Test with `connection_test.py` or similar

### Debugging Pipeline Failures
```bash
# Check specific stage:
python src/transcription/transcription_manager.py <audio_file>

# View database state:
sqlite3 project_memory.db "SELECT * FROM transcript LIMIT 1;"

# Server logs with full tracebacks:
python server.py  # uvicorn on port 8005

# CEP panel HTML console (F12 in browser):
# PANELWIN.html has localStorage debugging
```

---

## Project-Specific Patterns

### 1. **Few-Shot Learning via Style Templates** (Unique to This Project)
User provides reference video JSON. System stores in DB under `style_templates`:
```python
# In server.py::handle_adobe_analogy_request()
cursor.execute("""
    INSERT OR REPLACE INTO style_templates (style_name, style_type, reference_json)
    VALUES (?, ?, ?)
""", (style_name, style_type, json.dumps(parsed_reference_json)))
```

Then `keyword_director.py` fetches it:
```python
def fetch_style_analogy(chosen_style):
    cursor.execute("SELECT reference_json FROM style_templates WHERE style_type = ? LIMIT 1", (chosen_style,))
```

**This is NOT a traditional LLM few-shot approach** — it's template matching. Keep this in mind when extending.

### 2. **Dual Video Mode Support**
- `video_mode="Business"` (professional pacing)
- `video_mode="Educational"` (slower, more b-roll)
- System passes this from UI → server.py → main.py → keyword_director.py

### 3. **Prompt Optimization for Cost**
Images must stay <85 tokens to hit $0.004 cost tier:
```python
# In visualist_generator.py
class PromptOptimizer:
    def optimize_prompt(self, prompt: str) -> str:
        # Remove filler, compress adjectives, keep under 85 tokens
```

---

## Dependencies & External Services

| Service | Use | Failure Mode | Fallback |
|---------|-----|--------------|----------|
| Groq Cloud API | Transcription (Whisper) | Rate limit or downtime | Retry with next key in rotation |
| Pollinations API | Image generation | Down/slow | Stable Diffusion local API on port 7860 |
| Hugging Face API | Music generation (free tier) | Out of credits | Replicate API (paid) or silent placeholder |
| Adobe Premiere Pro | Timeline editing | Not installed/running | CEP panel won't work, but JSON output still valid |

---

## Performance Considerations

1. **Transcription Speed**: ~1 min audio = 2-3 seconds with Groq
2. **Image Generation**: ~1-2 seconds per image (Stable Diffusion local)
3. **Database Queries**: Always use SQLite (file-based, no network latency)
4. **Asset Path Storage**: Use relative paths internally, convert to absolute only for CEP
5. **Payload Size**: adobe_screenplay.json typically 3-10KB (JSX-safe)

---

## When to Modify vs. Add

| Scenario | Action |
|----------|--------|
| "Need different silence threshold" | Modify `DeadAirDetector.__init__()` default param |
| "Need new type of edit (dissolve variants)" | Add to `ScreenplayArchitect.add_transition()` + CEP |
| "Need to capture new audio metadata" | Add column to `transcript` table + update `groq_clients.py` |
| "Need new b-roll placement logic" | New function in `screenplay_architect.py`, new track in timeline |
| "Need custom subtitle styling" | Extend `subtitle_string` JSON in payload + CEP parsing |

---

## Documentation Files to Reference

- **`PROJECT_COMPLETION_SUMMARY.md`**: High-level feature overview & API keys needed
- **`INTEGRATION_COMPLETE.md`**: CEP panel communication protocol & path handling
- **`CEP_INTEGRATION_GUIDE.md`**: Deep dive on Premiere Pro timeline API
- **`IMPLEMENTATION_GUIDE.md`**: Architecture diagrams & module references

---

## Golden Rules for AI Agents

1. **Always validate before transmission**: Never send invalid JSON to CEP panel
2. **Respect the 5-stage pipeline**: Don't skip stages or reorder them
3. **Database first**: Query DB before calling APIs (avoid redundant API calls)
4. **Paths are critical**: Windows forward slashes, absolute paths only in output
5. **Fallback is mandatory**: Every external API needs a backup
6. **0.10s vocal padding is sacred**: Never change without understanding syllable clipping
7. **Test with integration suite**: Before marking any feature complete

---

Generated: 2025-05-25 | Last Updated: Current Build

