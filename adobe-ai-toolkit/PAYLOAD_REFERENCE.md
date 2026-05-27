# PAYLOAD REFERENCE CARD
## Quick lookup for all new parameters

---

## COMPLETE PAYLOAD STRUCTURE

```json
{
  "project_configuration": {
    "target_sequence_fps": 30,
    "global_vocal_padding_seconds": 0.10,
    "default_image_cost_tier_usd": 0.004
  },
  "timeline_data": {
    "cuts_and_trims": [ ... ],
    "video_track_1_vocals": [ ... ],
    "video_track_2_b_roll_images": [ ... ],
    "audio_track_1_vocals": [ ... ],
    "audio_track_2_music_beds": [ ... ]
  }
}
```

---

## DEAD AIR REMOVAL (cuts_and_trims)

### Structure
```json
{
  "type": "dead_air_removal",
  "start_timestamp": 5.0,
  "end_timestamp": 7.5,
  "action_execution": "ripple_delete"
}
```

### Processing in ExtendScript
```jsx
// All clips between start_timestamp and end_timestamp are deleted
// Remaining clips on timeline shift left automatically
performRippleDelete(sequence, 
    timeToTicks(5.0, fps),
    timeToTicks(7.5, fps)
);
```

### Result
- Removes filler, silence, or dead air segments
- Maintains timeline continuity
- Saves editing time manually

---

## VOCAL SEGMENTS with SUBTITLES & PADDING

### Structure
```json
{
  "original_start_time": 0.0,
  "original_end_time": 5.0,
  "padded_start_time": -0.1,
  "padded_end_time": 5.1,
  "subtitle_string": "Hello, welcome to this video!",
  "extracted_keywords": ["hello", "welcome", "video"],
  "duration_seconds": 5.2
}
```

### Key Fields

| Field | Type | Purpose |
|-------|------|---------|
| `original_start_time` | float | Actual speech start |
| `original_end_time` | float | Actual speech end |
| **`padded_start_time`** | float | **NEW**: Includes vocal padding buffer (usually -0.1s) |
| **`padded_end_time`** | float | **NEW**: Includes vocal padding buffer (usually +0.1s) |
| **`subtitle_string`** | string | **NEW**: Complete subtitle text for burning in |
| `extracted_keywords` | array | Keywords for search/metadata |
| `duration_seconds` | float | Total duration including padding |

### Why Padding?
- Provides buffer before and after speech starts
- Prevents audio clicks/pops at cut points
- Allows smoother crossfades in music beds
- Industry standard: 100-150ms on each side

### Processing in ExtendScript
```jsx
// Use padded times for audio operations, subtitles
var startTime = segment.padded_start_time;  // -0.1s
var endTime = segment.padded_end_time;      // 5.1s
var subtitle = segment.subtitle_string;     // "Hello..."

// Apply subtitle at padded times
applySubtitleBurnIn(sequence, subtitle, startTime, endTime, fps, keywords);
```

### Example
```
Original Speech:  [----------5s----------]
                 0.0                   5.0

With Padding:     [--0.1s--]  5s  [--0.1s--]
                  -0.1           5.1
```

---

## B-ROLL IMAGES with TRANSITIONS

### Structure
```json
{
  "asset_origin": "generated_image",
  "generation_prompt": "A cinematic landscape at golden hour",
  "start_timestamp": 0.0,
  "end_timestamp": 5.0,
  "duration_seconds": 5.0,
  "transition_behavior_in": "cross_dissolve",
  "transition_behavior_out": "fade"
}
```

### Key Fields

| Field | Type | Purpose |
|-------|------|---------|
| `asset_origin` | string | Where image came from |
| `generation_prompt` | string | What was generated |
| `start_timestamp` | float | Clip start time in timeline |
| `end_timestamp` | float | Clip end time in timeline |
| `duration_seconds` | float | Clip duration |
| **`transition_behavior_in`** | string | **NEW**: Transition at clip START |
| **`transition_behavior_out`** | string | **NEW**: Transition at clip END |

### Valid Transition Types
```
"cross_dissolve"  - Smooth blend between clips
"fade_to_black"   - Fade to and from black
"dip_to_white"    - Fade to and from white
"fade"            - Simple fade
"none"            - No transition
```

### Processing in ExtendScript
```jsx
// Apply transitions at both ends of clip
applyTransition(sequence, 
    timeToTicks(0.0, fps), 
    "cross_dissolve"  // transition_behavior_in
);

applyTransition(sequence,
    timeToTicks(5.0, fps),
    "fade"  // transition_behavior_out
);
```

### Transition Duration
- Default: 0.5 seconds (500ms)
- Applied symmetrically at start and end
- Can be customized per need

---

## AUDIO MUSIC BEDS with DUCKING

### Structure
```json
{
  "asset_origin": "generated_ambient_track",
  "style_descriptive_prompt": "Cinematic ambient with strings",
  "start_timestamp": 0.0,
  "end_timestamp": 10.0,
  "duration_seconds": 10.0,
  "base_volume_db": -18,
  "audio_ducking": {
    "active_while_vocals_playing": true,
    "attenuation_db": -12
  },
  "fade_in_seconds": 2.0,
  "fade_out_seconds": 1.5
}
```

### Key Fields

| Field | Type | Purpose |
|-------|------|---------|
| `asset_origin` | string | Type of asset |
| `style_descriptive_prompt` | string | Generation description |
| `start_timestamp` | float | Music starts |
| `end_timestamp` | float | Music ends |
| `base_volume_db` | float | Default volume (-18dB = quieter) |
| **`audio_ducking`** | object | **NEW**: Ducking configuration |
| **`active_while_vocals_playing`** | bool | **NEW**: Enable ducking during speech |
| **`attenuation_db`** | float | **NEW**: How much to reduce (-12dB typical) |
| `fade_in_seconds` | float | Music fade-in duration |
| `fade_out_seconds` | float | Music fade-out duration |

### Audio Ducking Explained

**Without Ducking:**
```
Music:  ████████████████████████████  (-18dB)
Vocals: ░░░░░░░░░░░░░░░░░░░░░░░░░░░░  (0dB)
Result: Both playing at full volume - vocals hard to hear
```

**With Ducking (-12dB attenuation):**
```
Music:  ████╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶  (-18dB → -30dB during vocals)
Vocals: ░░░░░░░░░░░░░░░░░░░░░░░░░░░░  (0dB)
Result: Music quieter during speech - vocals clear
```

### Processing in ExtendScript
```jsx
// Apply music bed with ducking
applyAudioVolume(sequence, 
    timeToTicks(0.0, fps),
    -18  // base_volume_db
);

// Apply ducking during vocal segments
applyAudioDucking(sequence,
    timeToTicks(0.0, fps),  // start
    timeToTicks(10.0, fps), // end
    -12,                    // attenuation_db
    fps
);

// Apply fades
applyAudioFade(sequence, timeToTicks(0.0, fps), 2.0, fps, "in");    // fade-in
applyAudioFade(sequence, timeToTicks(10.0, fps), 1.5, fps, "out");   // fade-out
```

### Decibel Reference
```
 0 dB  = Normal volume (unity gain)
-3 dB  = ~70% volume (subtle reduction)
-6 dB  = ~50% volume (noticeable reduction)
-12 dB = ~25% volume (significant reduction)
-18 dB = ~12% volume (very quiet)
-∞ dB  = Silence (muted)
```

---

## VOCAL AUDIO TRACK

### Structure
```json
{
  "asset_origin": "extracted_audio",
  "asset_path": "assets/extracted/vocal_segment_001.mp3",
  "start_timestamp": 0.0,
  "end_timestamp": 5.0,
  "duration_seconds": 5.0,
  "volume_db": 0
}
```

### Key Fields

| Field | Type | Purpose |
|-------|------|---------|
| `asset_origin` | string | "extracted_audio" or "text_to_speech" |
| `asset_path` | string | Full path to audio file |
| `start_timestamp` | float | When to play in timeline |
| `end_timestamp` | float | When to stop playing |
| `duration_seconds` | float | Clip length |
| `volume_db` | float | Playback volume (0 = normal) |

---

## PATH FORMATS

### Before Processing
```
assets/extracted/vocal_001.mp3       ← Relative
.\assets\ai_images\img_001.jpg       ← Windows relative
../assets/tts/voice.mp3              ← Relative with ..
```

### After Processing
```
C:/Users/dell/OneDrive/Desktop/auto--editor__AI/assets/extracted/vocal_001.mp3       ← Absolute
C:/Users/dell/OneDrive/Desktop/auto--editor__AI/assets/ai_images/img_001.jpg         ← Normalized
C:/Users/dell/OneDrive/Desktop/auto--editor__AI/assets/tts/voice.mp3                 ← Resolved
```

### Path Sanitization Rules
1. Backslash → Forward slash (Windows compatibility)
2. Relative → Absolute (using BASE_ASSET_PATH)
3. `..` resolved to actual path
4. Symlinks resolved
5. File existence verified

---

## METADATA FIELDS (Added by Server)

After server processing, payload includes:
```json
{
  "_metadata": {
    "version": "1.0",
    "timestamp": "2026-05-17T14:30:45.123456",
    "asset_base_path": "C:/Users/dell/OneDrive/Desktop/auto--editor__AI",
    "validation_status": "passed"
  }
}
```

---

## QUICK VALIDATION CHECKLIST

✓ **All New Parameters Present?**
- padded_start_time and padded_end_time in vocals
- transition_behavior_in and transition_behavior_out in B-roll
- audio_ducking with attenuation_db in music beds
- subtitle_string in vocal segments

✓ **All Paths Valid?**
- No backslashes in paths
- All paths are absolute
- All paths use forward slashes
- All files exist on disk

✓ **All Types Valid?**
- Transition types: cross_dissolve, fade_to_black, dip_to_white, fade, none
- Audio origins: generated_image, generated_ambient_track, extracted_audio, text_to_speech
- Decibel values: negative numbers (e.g., -18, -12, 0)

✓ **All Times Valid?**
- Timestamps in seconds (float)
- padded_end > padded_start
- Duration = padded_end - padded_start
- No NaN or infinite values

---

## INTEGRATION TEST RESULTS

All payload validations PASSED:
```
[PASS] Structure validation
[PASS] New parameters present (padded times, transitions, ducking, subtitles)
[PASS] Path sanitization (forward slashes, absolute paths)
[PASS] CEP transmission format (JSON serializable, JSX-safe)
[PASS] Invalid payload detection (catches errors)
[PASS] Transition type validation
[PASS] Subtitle extraction with timing
[PASS] Audio ducking values (-12dB valid)
```

---

## SUPPORT LINKS

- **Full Integration Guide**: CEP_INTEGRATION_GUIDE.md
- **Complete Summary**: INTEGRATION_COMPLETE.md
- **Test Suite**: integration_test_suite.py
- **Payload Validator**: src/data_formatter/payload_validator.py

