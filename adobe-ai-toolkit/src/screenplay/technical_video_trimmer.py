from typing import List, Dict, Any, Union, Tuple
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
from .dead_air_detector import DeadAirDetector
from .subtitle_generator import SubtitleGenerator


class ActionType(str, Enum):
    CUT_DEAD_AIR = "CUT_DEAD_AIR"
    GENERATE_SUBTITLE = "GENERATE_SUBTITLE"

class CutDeadAir(BaseModel):
    """Action to trim silences or filler words."""
    action: ActionType = ActionType.CUT_DEAD_AIR
    timestamp_start: float
    timestamp_end: float

class GenerateSubtitle(BaseModel):
    """Action to create short, perfectly timed caption chunks."""
    action: ActionType = ActionType.GENERATE_SUBTITLE
    chunk_id: int = Field(..., description="Sequential subtitle chunk identifier")
    text: str = Field(..., description="Subtitle text content")
    start_time: float = Field(..., description="Start timestamp in seconds")
    end_time: float = Field(..., description="End timestamp in seconds")

class TechnicalTimeline(BaseModel):
    """Agent 1 Output: Validated timeline of technical editing actions."""
    model_config = ConfigDict(populate_by_name=True)
    timeline: List[Union[CutDeadAir, GenerateSubtitle]]

def execute_technical_trimmer(
    word_timestamps: List[Dict[str, Any]],
    silence_intervals: List[Tuple[float, float]],
    video_duration: float
) -> TechnicalTimeline:
    """
    Agent 1: Technical Video Trimmer Pipeline
    Processes raw transcription and silence data to generate a validated technical timeline.
    """
    # Initialize components
    # We use a lower words_per_subtitle (e.g., 4) to ensure "short, perfectly timed caption chunks"
    dead_air_detector = DeadAirDetector()
    subtitle_gen = SubtitleGenerator(words_per_subtitle=4, max_line_width=30)

    # 1. Detect Dead Air (Silences + Filler Words)
    dead_air_detector.detect_from_silence_map(silence_intervals)
    dead_air_detector.detect_filler_words(transcript="", word_timestamps=word_timestamps)
    dead_air_detector.detect_trailing_silence(word_timestamps, video_duration)
    
    dead_air_zones = dead_air_detector.get_all_dead_air_zones()

    # 2. Generate Subtitles
    subtitle_blocks = subtitle_gen.generate_from_word_timestamps(word_timestamps)

    # 3. Build Timeline
    actions: List[Union[CutDeadAir, GenerateSubtitle]] = []

    # Add Cut Actions
    for start, end in dead_air_zones:
        actions.append(CutDeadAir(
            timestamp_start=round(start, 3),
            timestamp_end=round(end, 3)
        ))

    # Add Subtitle Actions
    for idx, sub in enumerate(subtitle_blocks):
        actions.append(GenerateSubtitle(
            chunk_id=idx,
            text=sub["subtitle_text"],
            start_time=round(sub["start_time"], 3),
            end_time=round(sub["end_time"], 3)
        ))

    # 4. Sort timeline by start time for Premiere Pro sequential processing
    actions.sort(key=lambda x: (
        x.timestamp_start if hasattr(x, 'timestamp_start') else x.start_time
    ))

    return TechnicalTimeline(timeline=actions)


__all__ = [
    'ActionType',
    'CutDeadAir',
    'GenerateSubtitle',
    'TechnicalTimeline',
    'execute_technical_trimmer'
]

