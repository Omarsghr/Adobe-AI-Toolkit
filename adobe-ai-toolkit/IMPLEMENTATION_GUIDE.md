"""
COMPREHENSIVE INTEGRATION GUIDE

Adobe-AI-Toolkit Panel Backend Architecture Upgrade
====================================================

This document describes the four major features implemented:

1. COMPREHENSIVE MULTI-MODAL UPGRADE
2. ADVANCED AUDIO INTELLIGENCE
3. KINETIC EDITING & SMOOTH SCREENPLAY LOGIC
4. INTEGRATED PIPELINE ORCHESTRATION


=== FEATURE 1: COMPREHENSIVE MULTI-MODAL UPGRADE ===

NEW MODULES:
- audio_music_generator.py: Generates background music and ambient tracks
- visualist_generator.py (UPDATED): PromptOptimizer class for cost-tier optimization

FLOW:
transcription_manager.py
    ↓
groq_clients.py (UPDATED: extracts word-level timestamps)
    ↓
keyword_director.py (NEW: uses ScreenplayArchitect)
    ↓
audio_music_generator.py (NEW: generates background tracks)
    ↓
visualist_generator.py (UPDATED: optimized prompt formatting)


TECHNICAL DETAILS:

A. Image Generation Optimization ($0.004 cost tier):
   - PromptOptimizer class in visualist_generator.py
   - Features:
     * Removes filler words ("very", "really", "absolutely")
     * Compresses adjective sequences
     * Keeps prompts under 85 tokens (~340 chars)
     * Uses Pollinations API (free tier)
   
   Usage:
   ```python
   optimizer = PromptOptimizer(cost_tier_usd=0.004)
   optimized = optimizer.optimize_prompt(raw_prompt)
   ```

B. Audio/Music Generation:
   - AudioMusicGenerator class in audio_music_generator.py
   - Features:
     * Hugging Face Inference API (free tier with HF token)
     * Replicate API support (optional)
     * Metadata creation for timeline integration
     * Duration estimation
   
   Usage:
   ```python
   generator = AudioMusicGenerator(output_dir="assets/ai_music")
   asset_path, duration = generator.generate_ambient_free(
       style_prompt="cinematic ambient with strings",
       duration_seconds=30.0,
       genre="ambient"
   )
   ```


=== FEATURE 2: ADVANCED AUDIO INTELLIGENCE ===

NEW MODULES:
- dead_air_detector.py: Detects silence and filler words
- subtitle_generator.py: Creates word-perfect subtitles
- groq_clients.py (UPDATED): Extracts word-level timestamps

FLOW:
transcription_manager.py
    ↓
groq_clients.py (extracts word_timestamps from Whisper verbose_json)
    ↓
dead_air_detector.py (processes timestamps)
    ↓
subtitle_generator.py (creates subtitle blocks)
    ↓
screenplay_architect.py (integrates into timeline)


TECHNICAL DETAILS:

A. Transcription with Word Timestamps:
   Updated groq_clients.py to extract word-level data from Whisper:
   - transcribe_with_groq() now calls _extract_word_timestamps()
   - Returns word_timestamps array with start/end times
   - Stored in map.json and available for downstream processing
   
   Output format:
   ```json
   {
     "word_timestamps": [
       {"word": "hello", "start": 0.0, "end": 0.5, "confidence": 0.99},
       {"word": "um", "start": 0.5, "end": 0.7, "confidence": 0.95},
       ...
     ]
   }
   ```

B. Dead Air Detection:
   - Silence zones > 0.5s detected from librosa analysis
   - Filler words detected from word_timestamps:
     * um, uh, uhh, umm, uhmm
     * like, you know, i mean, basically
     * so like, kind of, sort of, i guess
     * literally, actually, honestly, right
     * And pattern matching for stutters/repeated vowels
   - Trailing silence detection (> 1.0s after last word)
   - Zones merged and deduplicated
   
   Usage:
   ```python
   detector = DeadAirDetector(db_path)
   silence_zones = detector.detect_from_silence_map(silence_intervals)
   filler_zones = detector.detect_filler_words(transcript, word_timestamps)
   trailing = detector.detect_trailing_silence(word_timestamps, segment_end)
   report = detector.create_deletion_report()
   ```

C. Subtitle Generation:
   - Groups words into semantic subtitle blocks (6 words/block default)
   - Detects natural pauses (> 0.8s gaps) as block boundaries
   - Line-wrapping for on-screen display (42 char default width)
   - Automatic keyword extraction (words > 3 chars, excluding articles)
   - Exports to SRT and VTT formats
   
   Usage:
   ```python
   gen = SubtitleGenerator(words_per_subtitle=6, max_line_width=42)
   subtitles = gen.generate_from_word_timestamps(word_timestamps)
   gen.save_srt("subtitles.srt")
   gen.save_vtt("subtitles.vtt")
   report = gen.create_subtitle_report()
   ```


=== FEATURE 3: KINETIC EDITING & SMOOTH SCREENPLAY LOGIC ===

NEW MODULE:
- screenplay_architect.py: Core JSON timeline generator with cinematic features

FEATURES:
1. Mandatory 0.10s Vocal Padding:
   - Prevents syllable clipping on first/last words
   - Applied to start and end of all vocal segments
   
2. Explicit Transition Properties:
   - cross_dissolve (default for images)
   - fade_to_black
   - dip_to_white
   - fade
   - none
   
3. Audio Ducking Controls:
   - Integrated into music bed tracks
   - Active when vocals playing
   - Configurable attenuation (default -12dB)
   
4. Timeline Architecture:
   - cuts_and_trims: Dead air removal zones
   - video_track_1_vocals: Vocal segments with padding
   - video_track_2_b_roll_images: Images with transitions
   - audio_track_1_vocals: TTS or extracted audio
   - audio_track_2_music_beds: Background music with ducking

USAGE:

```python
from screenplay_architect import ScreenplayArchitect

architect = ScreenplayArchitect(vocal_padding_seconds=0.10, fps=30)

# Add dead air zones for deletion
architect.add_dead_air_removal(start_ts=5.0, end_ts=5.5)

# Add vocal segments with automatic padding
architect.add_vocal_segment(
    start_time=0.5,
    end_time=3.2,
    subtitle_text="This is the spoken text",
    keywords=["spoken", "text"]
)

# Add B-roll with transitions
architect.add_b_roll_image(
    generation_prompt="Professional office environment",
    start_ts=0.0,
    end_ts=3.0,
    transition_in="cross_dissolve",
    transition_out="fade"
)

# Add music bed with ducking
architect.add_music_bed(
    style_prompt="Cinematic ambient strings",
    start_ts=0.0,
    end_ts=120.0,
    base_volume_db=-18,
    fade_in_seconds=2.0,
    fade_out_seconds=1.5,
    ducking_attenuation_db=-12
)

# Export to Premiere Pro
architect.save_to_file("adobe_screenplay.json")
```

OUTPUT JSON STRUCTURE:

```json
{
  "project_configuration": {
    "target_sequence_fps": 30,
    "global_vocal_padding_seconds": 0.10,
    "default_image_cost_tier_usd": 0.004
  },
  "timeline_data": {
    "cuts_and_trims": [
      {
        "type": "dead_air_removal",
        "start_timestamp": 5.000,
        "end_timestamp": 5.500,
        "action_execution": "ripple_delete"
      }
    ],
    "video_track_1_vocals": [
      {
        "original_start_time": 0.500,
        "original_end_time": 3.200,
        "padded_start_time": 0.400,
        "padded_end_time": 3.300,
        "subtitle_string": "This is the spoken text",
        "extracted_keywords": ["spoken", "text"],
        "duration_seconds": 2.900
      }
    ],
    "video_track_2_b_roll_images": [
      {
        "asset_origin": "generated_image",
        "generation_prompt": "Professional office environment",
        "start_timestamp": 0.000,
        "end_timestamp": 3.000,
        "duration_seconds": 3.000,
        "transition_behavior_in": "cross_dissolve",
        "transition_behavior_out": "fade"
      }
    ],
    "audio_track_2_music_beds": [
      {
        "asset_origin": "generated_ambient_track",
        "style_descriptive_prompt": "Cinematic ambient strings",
        "start_timestamp": 0.000,
        "end_timestamp": 120.000,
        "duration_seconds": 120.000,
        "base_volume_db": -18,
        "audio_ducking": {
          "active_while_vocals_playing": true,
          "attenuation_db": -12
        },
        "fade_in_seconds": 2.000,
        "fade_out_seconds": 1.500
      }
    ]
  }
}
```


=== FEATURE 4: INTEGRATED PIPELINE ORCHESTRATION ===

UPDATED MODULE:
- master_glue.py: Now orchestrates 5 steps (was 3)

NEW PIPELINE FLOW:

Step 1: Extract Audio
  → audio_processor.py

Step 2: Transcribe with Word Timestamps
  → transcription_manager.py + groq_clients.py (UPDATED)
  → Outputs: full transcript + word_timestamps array

Step 3: Audio Intelligence
  → signal_processor.py (silence detection)
  → dead_air_detector.py (NEW: filler words, trailing silence)
  → Database: dead_air_zones table

Step 4: Kinetic Screenplay Generation
  → keyword_director.py (UPDATED: uses ScreenplayArchitect)
  → audio_music_generator.py (NEW: music generation)
  → Outputs: adobe_screenplay.json (NEW FORMAT)

Step 5: Visual Asset Generation
  → visualist_generator.py (UPDATED: prompt optimization)
  → Database: generated_assets table with cost tracking


EXECUTION:

```bash
python src/data_formatter/master_glue.py
```

Or individually:

```python
# Step 1-2: Transcription
python src/transcription/transcription_manager.py

# Step 3: Audio Analysis
python src/signal_analysis/signal_processor.py

# Step 4: Screenplay
python src/ai_logic/keyword_director.py

# Step 5: Images
python -c "from src.ai_logic.visualist_generator import generate_and_store_free; generate_and_store_free()"
```


=== INTEGRATION WITH ADOBE PREMIERE PRO CEP EXTENSION ===

The new screenplay JSON format is designed for seamless CEP panel parsing:

1. Dead Air Removal:
   ```jsx
   screenplay.timeline_data.cuts_and_trims.forEach(cut => {
       if (cut.type === "dead_air_removal") {
           // Ripple delete from cut.start_timestamp to cut.end_timestamp
       }
   });
   ```

2. Vocal Segments with Padding:
   ```jsx
   screenplay.timeline_data.video_track_1_vocals.forEach(vocal => {
       // Place audio from padded_start_time to padded_end_time
       // Add subtitles: subtitle_string
       // Extract keywords for metadata
   });
   ```

3. B-Roll with Transitions:
   ```jsx
   screenplay.timeline_data.video_track_2_b_roll_images.forEach(image => {
       // Apply transition_behavior_in (cross_dissolve, fade_to_black, etc.)
       // Apply transition_behavior_out
       // Auto-generate via: image.generation_prompt
   });
   ```

4. Audio Ducking:
   ```jsx
   screenplay.timeline_data.audio_track_2_music_beds.forEach(music => {
       // Set base volume: music.base_volume_db
       // When vocals active, apply: music.audio_ducking.attenuation_db
       // Fade in: music.fade_in_seconds
       // Fade out: music.fade_out_seconds
   });
   ```


=== CONFIGURATION & ENVIRONMENT ===

Required .env variables:

```
GROQ_API_KEY_1=your_groq_key_1
GROQ_API_KEY_2=your_groq_key_2
... (up to 15 keys supported)
HUGGINGFACE_API_KEY=your_hf_token  (optional, for music generation)
REPLICATE_API_KEY=your_replicate_key  (optional, for Riffusion)
```

Database Tables:

```
project_memory.db:
  - transcript (full_text, method_used)
  - silence_map (start REAL, end REAL)
  - dead_air_zones (start REAL, end REAL, reason TEXT)
  - generated_assets (id, keyword, local_path, prompt_used, optimized_prompt, cost_estimate_usd)
```


=== SUMMARY OF CHANGES ===

FILES CREATED:
✓ src/screenplay/__init__.py
✓ src/screenplay/screenplay_architect.py
✓ src/screenplay/audio_music_generator.py
✓ src/screenplay/dead_air_detector.py
✓ src/screenplay/subtitle_generator.py

FILES UPDATED:
✓ src/transcription/groq_clients.py (added word-level timestamp extraction)
✓ src/ai_logic/visualist_generator.py (added PromptOptimizer class)
✓ src/ai_logic/keyword_director.py (updated to use ScreenplayArchitect)
✓ src/data_formatter/master_glue.py (expanded to 5-step pipeline)

FEATURES DELIVERED:
✓ 0.10s vocal padding on all clips
✓ Explicit transition properties (cross_dissolve, fade, etc.)
✓ Audio ducking with configurable attenuation
✓ Word-level transcription with timestamps
✓ Filler word detection (um, uh, like, etc.)
✓ Dead air zone detection and reporting
✓ Word-perfect subtitle generation (SRT/VTT export)
✓ Optimized image prompts for $0.004 cost tier
✓ Background music generation with ducking
✓ Integrated database tracking
✓ Seamless CEP panel integration ready


=== NEXT STEPS FOR CEP PANEL DEVELOPMENT ===

1. Import the screenplay_architect module in your JSX panel
2. Parse the adobe_screenplay.json file
3. Implement the dead_air_removal logic (ripple delete)
4. Create native Premiere Pro references for each vocal segment
5. Apply transitions via adjustmentClips or similar methods
6. Implement audio ducking on music track during vocal segments
7. Add subtitle layer with extracted text
8. Test with sample Adobe Premiere Pro project
"""
