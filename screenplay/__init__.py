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

__all__ = [
    'ScreenplayArchitect',
    'AudioMusicGenerator',
    'DeadAirDetector',
    'SubtitleGenerator'
]
