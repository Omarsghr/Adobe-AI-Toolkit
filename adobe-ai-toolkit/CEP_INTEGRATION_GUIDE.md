# CEP EXTENSION INTEGRATION GUIDE
## Backend-to-Frontend-to-Timeline Complete Pipeline

---

## ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────┐
│ ADOBE PREMIERE PRO PANEL (HTML + JavaScript)                    │
│ └─ PANELWIN.html: UI, server config, file selection             │
│ └─ CEP Bridge: Communicates with ExtendScript                   │
└──────────────────┬──────────────────────────────────────────────┘
                   │ (HTTP POST with multipart/form-data)
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│ BACKEND API SERVER (FastAPI on 0.0.0.0:8000)                   │
│ └─ server.py: Orchestrates pipeline + validates payload         │
│ └─ main.py: Master glue coordinates all processing steps        │
│ └─ payload_validator.py: Cleans paths, validates structure      │
└──────────────────┬──────────────────────────────────────────────┘
                   │ (JSON screenplay with all new parameters)
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│ CEP PANEL (JavaScript) RECEIVES PAYLOAD                         │
│ └─ Parses JSON with new fields:                                 │
│    • padded_start_time, padded_end_time                         │
│    • transition_behavior_in, transition_behavior_out            │
│    • audio_ducking with attenuation_db                          │
│    • subtitle_string for each vocal segment                     │
└──────────────────┬──────────────────────────────────────────────┘
                   │ (CEP evalScript call with serialized payload)
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│ EXTENDSCRIPT (host.jsx) INGESTION ENGINE                        │
│ └─ applyScreenplayToTimeline(payload)                           │
│    1. Validates payload structure                               │
│    2. Performs ripple deletes for dead air zones               │
│    3. Applies transitions (cross dissolve, fade, etc.)          │
│    4. Handles audio ducking with attenuation                    │
│    5. Burns in subtitles with precise timestamps                │
└──────────────────┬──────────────────────────────────────────────┘
                   │ (Native Premiere Pro API calls)
                   ▼
          ✨ TIMELINE UPDATED ✨
```

---

## INSTALLATION STEPS

### 1. FILE STRUCTURE
```
CEP/
├── manifest.xml              # CEP extension configuration
├── PANELWIN.html             # Frontend panel UI & API communication
├── host.jsx                  # ExtendScript for timeline ingestion
└── assets/
    ├── icon_normal.png
    ├── icon_dark.png
    ├── icon_normal_hires.png
    └── icon_dark_hires.png
```

### 2. PREMIERE PRO PANEL INSTALLATION

#### Windows:
1. Navigate to:
   ```
   C:\Program Files\Adobe\Common\Media\CEP\extensions\
   ```

2. Create a folder: `com.adobe.ai_toolkit`

3. Copy the entire `CEP/` folder contents into it

4. Restart Premiere Pro

5. Go to **Window → Extensions → Adobe AI Toolkit**

#### Mac:
```
~/Library/Application Support/Adobe/CEP/extensions/
```

### 3. SERVER SETUP

1. Ensure `server.py` is running:
   ```bash
   python server.py
   ```

2. Server will start on `0.0.0.0:8000`

3. Panel will connect to server at configured IP/port

---

## PAYLOAD STRUCTURE (DETAILED)

### Input Payload from Backend

The backend generates a JSON screenplay with this complete structure:

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
        "start_timestamp": 5.0,
        "end_timestamp": 7.5,
        "action_execution": "ripple_delete"
      }
    ],
    "video_track_1_vocals": [
      {
        "original_start_time": 0.0,
        "original_end_time": 5.0,
        "padded_start_time": -0.1,      // NEW: padding for smooth audio
        "padded_end_time": 5.1,         // NEW: padding for smooth audio
        "subtitle_string": "Hello, welcome to the video!",  // NEW: subtitle text
        "extracted_keywords": ["hello", "welcome"],
        "duration_seconds": 5.2
      }
    ],
    "video_track_2_b_roll_images": [
      {
        "asset_origin": "generated_image",
        "generation_prompt": "A beautiful landscape at sunset",
        "start_timestamp": 0.0,
        "end_timestamp": 5.0,
        "duration_seconds": 5.0,
        "transition_behavior_in": "cross_dissolve",   // NEW: transition type
        "transition_behavior_out": "fade"             // NEW: exit transition
      }
    ],
    "audio_track_1_vocals": [
      {
        "asset_origin": "extracted_audio",
        "asset_path": "assets/extracted/vocal_segment_1.mp3",
        "start_timestamp": 0.0,
        "end_timestamp": 5.0,
        "duration_seconds": 5.0,
        "volume_db": 0
      }
    ],
    "audio_track_2_music_beds": [
      {
        "asset_origin": "generated_ambient_track",
        "style_descriptive_prompt": "Ambient cinematic background with strings",
        "start_timestamp": 0.0,
        "end_timestamp": 10.0,
        "duration_seconds": 10.0,
        "base_volume_db": -18,
        "audio_ducking": {              // NEW: ducking settings
          "active_while_vocals_playing": true,
          "attenuation_db": -12         // NEW: reduction amount
        },
        "fade_in_seconds": 2.0,
        "fade_out_seconds": 1.5
      }
    ]
  }
}
```

---

## KEY INTEGRATION POINTS

### 1. PAYLOAD VALIDATION (server.py)

```python
cleaned_payload = PayloadFormatter.prepare_for_transmission(
    screenplay_payload,
    BASE_ASSET_PATH
)
```

**What it does:**
- ✓ Validates all required fields are present
- ✓ Converts backslashes → forward slashes in paths
- ✓ Resolves relative paths to absolute
- ✓ Verifies all referenced files exist
- ✓ Adds `_metadata` with validation status

**Error handling:**
- If validation fails, returns descriptive error
- Missing files logged with exact paths
- Invalid transitions caught at server-side

### 2. FRONTEND PAYLOAD RECEPTION (PANELWIN.html)

```javascript
const data = await response.json();
this.currentPayload = data.data;  // Complete, clean payload
```

**Payload Access:**
```javascript
// Vocal segments with padding and subtitles
const vocals = payload.timeline_data.video_track_1_vocals;
vocals.forEach(v => {
    console.log(`Subtitle: "${v.subtitle_string}"`);
    console.log(`Padded: ${v.padded_start_time}s - ${v.padded_end_time}s`);
});

// B-roll with transitions
const images = payload.timeline_data.video_track_2_b_roll_images;
images.forEach(img => {
    console.log(`Transition IN: ${img.transition_behavior_in}`);
    console.log(`Transition OUT: ${img.transition_behavior_out}`);
});

// Music with ducking
const music = payload.timeline_data.audio_track_2_music_beds;
music.forEach(m => {
    console.log(`Ducking: ${m.audio_ducking.attenuation_db}dB`);
});
```

### 3. EXTENDSCRIPT TIMELINE INGESTION (host.jsx)

#### Dead Air Ripple Delete
```jsx
performRippleDelete(sequence, startTicks, endTicks);
```
- Finds all clips in the dead air zone
- Deletes them with ripple enabled
- Remaining clips shift left automatically

#### Transition Application
```jsx
applyTransition(sequence, clipStartTicks, "cross_dissolve", 0.5);
```
- Maps transition names to Premiere IDs
- Valid types: `cross_dissolve`, `fade_to_black`, `dip_to_white`, `fade`, `none`
- Applies to video track 1 clips

#### Audio Ducking
```jsx
applyAudioDucking(sequence, startTicks, endTicks, -12, fps);
```
- Reduces music bed volume by `attenuation_db` during vocals
- Smooth volume curve using keyframes
- Restores base volume after vocal segment

#### Subtitle Burn-in
```jsx
applySubtitleBurnIn(
    sequence,
    "Hello, welcome!",
    0.0,
    5.0,
    30,
    ["hello", "welcome"]
);
```
- Creates text graphic on highest video track
- Positions at `padded_start_time` to `padded_end_time`
- Keywords stored for search/metadata

---

## FILE PATH RESOLUTION STRATEGY

### Problem
Backend generates files in various locations. Frontend/ExtendScript need exact paths.

### Solution: PayloadValidator.sanitize_paths()

```
Input: "assets/ai_images/generated_001.png"
       └─ Relative path

Processing:
1. Check if relative → make absolute within BASE_ASSET_PATH
2. Normalize backslashes to forward slashes (Windows compatibility)
3. Resolve symlinks and ".." references
4. Verify file exists

Output: "C:/Users/DELL/OneDrive/Desktop/auto--editor__AI/assets/ai_images/generated_001.png"
        └─ Clean, absolute, verified path
```

### Asset Origin to Path Mapping

| Asset Origin | Directory | Example |
|---|---|---|
| `generated_image` | `assets/ai_images/` | `assets/ai_images/img_001.jpg` |
| `generated_ambient_track` | `assets/ai_music/` | `assets/ai_music/ambient_001.wav` |
| `text_to_speech` | `assets/tts/` | `assets/tts/voice_001.mp3` |
| `extracted_audio` | `assets/extracted/` | `assets/extracted/vocal_001.mp3` |

---

## ERROR HANDLING CHECKLIST

### Backend Errors
- ✓ File upload fails → Return 500 with clear message
- ✓ Pipeline crashes → Caught and logged
- ✓ Payload invalid → Validation error with field name
- ✓ Assets missing → Warning logged, paths provided for debugging

### Frontend Errors
- ✓ Network unreachable → Status shows connection error
- ✓ Invalid server response → JSON parse error caught
- ✓ Empty file selected → User warning, button disabled

### ExtendScript Errors
- ✓ No active sequence → Alert before processing
- ✓ Clip not found → Skipped with warning
- ✓ File doesn't exist → Graceful skip with path logged
- ✓ Transition invalid → Falls back to cross_dissolve

---

## TESTING WORKFLOW

### 1. Test Backend Payload Generation
```bash
python main.py --test-payload
```
Outputs: `adobe_screenplay.json`

### 2. Validate Payload Structure
```python
from src.data_formatter.payload_validator import PayloadValidator
import json

with open("adobe_screenplay.json") as f:
    payload = json.load(f)

is_valid, errors = PayloadValidator.validate_structure(payload)
print("Valid:", is_valid)
print("Errors:", errors)
```

### 3. Test Server Endpoint
```bash
curl -X POST \
  -F "file=@test_audio.mp3" \
  http://localhost:8000/process-from-adobe
```

Response should include all new parameters with clean paths.

### 4. Test Panel UI
1. Open Premiere Pro
2. Load panel (Window → Extensions → Adobe AI Toolkit)
3. Enter server IP/port
4. Click "Test Connection"
5. Select audio file
6. Click "Process & Apply to Timeline"
7. Monitor status display for all steps

### 5. Verify Timeline Changes
In Premiere Pro, check:
- [ ] Dead air zones deleted with ripple shift
- [ ] Transitions applied to B-roll clips
- [ ] Music volume reduced during vocals
- [ ] Subtitles visible at correct timestamps

---

## DEBUGGING TIPS

### Check Server Logs
```bash
# Terminal where server.py is running
❌ Error messages show exact failure point
✅ "Payload ready for transmission" = success
```

### Inspect Frontend Network Traffic
1. Open browser DevTools (F12)
2. Network tab
3. Look for POST to `/process-from-adobe`
4. Response should have all new parameters

### Verify File Paths
```python
import os
from src.data_formatter.payload_validator import PayloadValidator

payload = {...}
PayloadValidator.sanitize_paths(payload, "/base/path")

# Check if paths are now absolute and valid
for image in payload['timeline_data']['video_track_2_b_roll_images']:
    path = image['asset_path']
    exists = os.path.exists(path)
    print(f"{path}: {'✓' if exists else '✗'}")
```

### Test ExtendScript Directly
In Premiere Pro's ESTK (ExtendScript Toolkit):
```jsx
var testPayload = {
    project_configuration: { target_sequence_fps: 30, global_vocal_padding_seconds: 0.10 },
    timeline_data: { cuts_and_trims: [], video_track_1_vocals: [], ... }
};
applyScreenplayToTimeline(testPayload);
```

---

## COMMON ISSUES & SOLUTIONS

| Issue | Cause | Solution |
|---|---|---|
| "No active sequence" | Premiere Pro setup | Create new sequence first |
| Files not found in path | Backslashes on Windows | PayloadValidator handles auto-normalization |
| Transitions not applying | Invalid transition type | Check VALID_TRANSITIONS list in code |
| Audio ducking not working | Audio track index wrong | Verify track numbers in JSX |
| Subtitles not visible | No graphics track | Create titles track in sequence |
| Server 500 error | Pipeline crash | Check backend logs, verify audio format |

---

## NEXT STEPS

1. **Test the complete pipeline with a real audio file**
2. **Verify all timeline changes are applied correctly**
3. **Fine-tune transition durations and audio ducking amounts**
4. **Add more transition types as needed**
5. **Implement subtitle styling (font, size, color)**
6. **Add real-time progress reporting to panel**

