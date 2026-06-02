"""
Screenplay Generation Module

Handles the transformation of raw transcription data into
cinematic screenplay JSON with kinetic editing features:
- Vocal padding (0.10s safety anchors)
- Transition properties (cross_dissolve, fade, etc.)
- Audio ducking controls
- Dead air & filler word detection
- Word-perfect subtitle generation
"""

from .screenplay_architect import ScreenplayArchitect
from .audio_music_generator import AudioMusicGenerator
from .dead_air_detector import DeadAirDetector
from .subtitle_generator import SubtitleGenerator
from .technical_video_trimmer import TechnicalTimeline, execute_technical_trimmer
from .creative_director import CreativeDecisions, execute_creative_director
from .multi_agent_pipeline import (
    run_video_automation_pipeline,
    validate_pipeline_output,
    PipelineOutput,
    TranscriptData
)

__all__ = [
    'ScreenplayArchitect',
    'AudioMusicGenerator',
    'DeadAirDetector',
    'SubtitleGenerator',
    'TechnicalTimeline',
    'execute_technical_trimmer',
    'CreativeDecisions',
    'execute_creative_director',
    'run_video_automation_pipeline',
    'validate_pipeline_output',
    'PipelineOutput',
    'TranscriptData'
]
