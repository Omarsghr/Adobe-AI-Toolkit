from typing import List, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class CreativeActionType(str, Enum):
    APPLY_ZOOM_PUNCH_IN = "APPLY_ZOOM_PUNCH_IN"
    BACKGROUND_MUSIC_CUE = "BACKGROUND_MUSIC_CUE"


class ZoomPunchIn(BaseModel):
    """Action to apply kinetic zoom punch-in effect at key moments."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "action": "APPLY_ZOOM_PUNCH_IN",
                "timestamp": 5.2,
                "zoom_level": 1.15
            }
        }
    )
    action: CreativeActionType = CreativeActionType.APPLY_ZOOM_PUNCH_IN
    timestamp: float = Field(..., description="Timestamp in seconds where zoom begins")
    zoom_level: float = Field(..., description="Zoom multiplier (e.g., 1.15 = 15% zoom)")


class VolumeEnvelopePoint(BaseModel):
    """Single point in volume automation curve."""
    timestamp: float = Field(..., description="Time in seconds")
    volume_level: float = Field(..., ge=0.0, le=1.0, description="Volume 0.0-1.0")


class BackgroundMusicCue(BaseModel):
    """Action to layer background music with dynamic volume envelope."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "action": "BACKGROUND_MUSIC_CUE",
                "track_style": "ambient_cinematic",
                "volume_envelope": [
                    {"timestamp": 0.0, "volume_level": 0.0},
                    {"timestamp": 2.0, "volume_level": 0.6},
                    {"timestamp": 10.0, "volume_level": 0.4}
                ]
            }
        }
    )
    action: CreativeActionType = CreativeActionType.BACKGROUND_MUSIC_CUE
    track_style: str = Field(..., description="Music genre/mood (e.g., 'ambient_cinematic', 'upbeat_corporate')")
    volume_envelope: List[Dict[str, float]] = Field(
        ...,
        description="List of {timestamp: volume} mappings for automation"
    )


class CreativeDecisions(BaseModel):
    """Agent 2 Output: Creative directing choices linked to technical timeline."""
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "creative_actions": [
                    {"action": "APPLY_ZOOM_PUNCH_IN", "timestamp": 2.5, "zoom_level": 1.12},
                    {"action": "BACKGROUND_MUSIC_CUE", "track_style": "upbeat_corporate", "volume_envelope": []}
                ],
                "mood": "inspiring",
                "video_mode": "Business"
            }
        }
    )
    creative_actions: List[Union[ZoomPunchIn, BackgroundMusicCue]] = Field(
        ...,
        description="Ordered list of creative directives applied to the technical timeline"
    )
    mood: str = Field(..., description="Overall emotional tone of the piece")
    video_mode: str = Field(default="Business", description="Video style ('Business', 'Educational')")


def execute_creative_director(
    technical_timeline: Dict[str, Any],
    mood: str,
    video_mode: str = "Business",
    intensity_multiplier: float = 1.0
) -> CreativeDecisions:
    """
    Agent 2: Creative Director Pipeline
    Transforms technical timeline into cinematic creative directives.

    Args:
        technical_timeline: Output dict from execute_technical_trimmer
        mood: Emotional tone ('inspiring', 'dramatic', 'calm', 'energetic')
        video_mode: Style mode ('Business' or 'Educational')
        intensity_multiplier: Scaling factor for effect intensities [0.5 - 2.0]

    Returns:
        CreativeDecisions: Validated creative actions
    """

    creative_actions: List[Union[ZoomPunchIn, BackgroundMusicCue]] = []

    # Extract timeline for analysis
    actions = technical_timeline.get("timeline", [])

    # Mood-based creative rules
    mood_presets: Dict[str, Dict[str, Any]] = {
        "inspiring": {"zoom": 1.15, "music_style": "upbeat_cinematic", "base_volume": 0.6},
        "dramatic": {"zoom": 1.25, "music_style": "dramatic_tension", "base_volume": 0.7},
        "calm": {"zoom": 1.05, "music_style": "ambient_peaceful", "base_volume": 0.4},
        "energetic": {"zoom": 1.20, "music_style": "upbeat_corporate", "base_volume": 0.65},
    }

    preset = mood_presets.get(mood, mood_presets["inspiring"])
    preset["zoom"] *= intensity_multiplier
    preset["base_volume"] = min(1.0, preset["base_volume"] * intensity_multiplier)

    # Extract key moments from subtitle actions (emotional peaks)
    subtitle_actions = [a for a in actions if a.get("action") == "GENERATE_SUBTITLE"]

    # Apply zoom punch-in at every 3rd subtitle for pacing
    for idx, subtitle in enumerate(subtitle_actions):
        if idx % 3 == 0:
            creative_actions.append(
                ZoomPunchIn(
                    timestamp=round(subtitle.get("timestamp_start", 0.0) + 0.1, 3),
                    zoom_level=preset["zoom"]
                )
            )

    # Add background music with dynamic envelope
    if subtitle_actions:
        first_ts = subtitle_actions[0].get("timestamp_start", 0.0)
        last_ts = subtitle_actions[-1].get("timestamp_end", 0.0)

        # Build volume envelope: fade in, sustain, fade out
        volume_envelope = [
            {"timestamp": max(0.0, first_ts - 1.0), "volume_level": 0.0},
            {"timestamp": first_ts, "volume_level": preset["base_volume"]},
            {"timestamp": last_ts, "volume_level": preset["base_volume"]},
            {"timestamp": last_ts + 1.0, "volume_level": 0.0},
        ]

        creative_actions.append(
            BackgroundMusicCue(
                track_style=preset["music_style"],
                volume_envelope=volume_envelope
            )
        )

    # Sort by timestamp for sequential execution
    creative_actions.sort(
        key=lambda x: (
            x.timestamp if isinstance(x, ZoomPunchIn) else x.volume_envelope[0].get("timestamp", 0.0)
        )
    )

    return CreativeDecisions(
        creative_actions=creative_actions,
        mood=mood,
        video_mode=video_mode
    )

