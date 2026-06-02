from typing import Dict, List, Any, Tuple, Optional
from pydantic import BaseModel, Field, ValidationError, ConfigDict
from .technical_video_trimmer import execute_technical_trimmer
from .creative_director import execute_creative_director


class TranscriptData(BaseModel):
    """Validated input schema for video automation pipeline."""
    word_timestamps: List[Dict[str, Any]] = Field(
        ...,
        description="Word-level timing data: [{'word': str, 'start': float, 'end': float, 'confidence': float}]"
    )
    silence_intervals: List[Tuple[float, float]] = Field(
        default_factory=list,
        description="Detected silence zones [(start, end), ...]"
    )
    video_duration: float = Field(..., gt=0, description="Total video length in seconds")
    full_transcript: Optional[str] = Field(default=None, description="Complete transcript text")


class PipelineOutput(BaseModel):
    """Final output of the multi-agent video automation pipeline."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "technical_timeline": {
                    "timeline": [
                        {"action": "CUT_DEAD_AIR", "timestamp_start": 2.5, "timestamp_end": 3.2},
                        {"action": "GENERATE_SUBTITLE", "chunk_id": 0, "text": "Example subtitle", "start_time": 0.0, "end_time": 2.5}
                    ]
                },
                "creative_decisions": {
                    "creative_actions": [
                        {"action": "APPLY_ZOOM_PUNCH_IN", "timestamp": 5.0, "zoom_level": 1.15}
                    ],
                    "mood": "inspiring",
                    "video_mode": "Business"
                },
                "execution_metadata": {
                    "total_actions_generated": 5,
                    "technical_actions_count": 3,
                    "creative_actions_count": 2,
                    "dead_air_zones_removed": 1,
                    "subtitles_generated": 2,
                    "pipeline_status": "success",
                    "validation_errors": []
                }
            }
        }
    )
    technical_timeline: Dict[str, Any] = Field(..., description="Agent 1 technical editing actions")
    creative_decisions: Dict[str, Any] = Field(..., description="Agent 2 creative directives")
    execution_metadata: Dict[str, Any] = Field(
        ...,
        description="Pipeline execution stats and validation results"
    )


def run_video_automation_pipeline(
    transcript_data: Dict[str, Any],
    mood: str,
    video_mode: str = "Business",
    intensity_multiplier: float = 1.0,
    enable_validation: bool = True
) -> Dict[str, Any]:
    """
    Main Orchestration Function: Multi-Agent Video Automation Pipeline

    Coordinates Agent 1 (Technical Trimmer) and Agent 2 (Creative Director)
    to transform raw transcript data into a production-ready cinematic screenplay.

    Args:
        transcript_data: Raw video metadata and timing
            Required keys: word_timestamps (list), video_duration (float)
            Optional keys: silence_intervals (list), full_transcript (str)
        mood: Creative mood ('inspiring', 'dramatic', 'calm', 'energetic')
        video_mode: Target style ('Business', 'Educational')
        intensity_multiplier: Effect intensity scaling [0.5 - 2.0]
        enable_validation: Enable strict Pydantic validation

    Returns:
        Dict[str, Any]: JSON-ready output with technical + creative actions + metadata

    Raises:
        ValidationError: If transcript_data fails Pydantic validation (if enabled)
        ValueError: If transcript_data is missing critical fields
    """

    execution_stats = {
        "total_actions_generated": 0,
        "technical_actions_count": 0,
        "creative_actions_count": 0,
        "dead_air_zones_removed": 0,
        "subtitles_generated": 0,
        "pipeline_status": "processing",
        "validation_errors": [],
        "warnings": [],
    }

    try:
        # Stage 1: Validate Input Data
        if enable_validation:
            try:
                validated_transcript = TranscriptData(**transcript_data)
            except ValidationError as e:
                execution_stats["pipeline_status"] = "validation_failed"
                execution_stats["validation_errors"] = [str(err) for err in e.errors()]
                return _build_error_output(execution_stats)
        else:
            # Manual validation if Pydantic validation disabled
            if "word_timestamps" not in transcript_data or "video_duration" not in transcript_data:
                raise ValueError("Missing required keys: word_timestamps, video_duration")

            validated_transcript = TranscriptData(
                word_timestamps=transcript_data.get("word_timestamps", []),
                silence_intervals=transcript_data.get("silence_intervals", []),
                video_duration=transcript_data.get("video_duration"),
                full_transcript=transcript_data.get("full_transcript")
            )

        # Stage 2: Execute Agent 1 - Technical Video Trimmer
        technical_timeline = execute_technical_trimmer(
            word_timestamps=validated_transcript.word_timestamps,
            silence_intervals=validated_transcript.silence_intervals,
            video_duration=validated_transcript.video_duration
        )

        # Extract stats from technical timeline
        timeline_actions = technical_timeline.timeline
        execution_stats["technical_actions_count"] = len(timeline_actions)
        execution_stats["dead_air_zones_removed"] = sum(
            1 for a in timeline_actions if a.action.value == "CUT_DEAD_AIR"
        )
        execution_stats["subtitles_generated"] = sum(
            1 for a in timeline_actions if a.action.value == "GENERATE_SUBTITLE"
        )

        # Stage 3: Execute Agent 2 - Creative Director
        creative_decisions = execute_creative_director(
            technical_timeline=technical_timeline.model_dump(),
            mood=mood,
            video_mode=video_mode,
            intensity_multiplier=intensity_multiplier
        )

        # Extract stats from creative decisions
        execution_stats["creative_actions_count"] = len(creative_decisions.creative_actions)
        execution_stats["total_actions_generated"] = (
            execution_stats["technical_actions_count"] +
            execution_stats["creative_actions_count"]
        )

        # Stage 4: Compile Output
        execution_stats["pipeline_status"] = "success"

        output = PipelineOutput(
            technical_timeline=technical_timeline.model_dump(),
            creative_decisions=creative_decisions.model_dump(),
            execution_metadata=execution_stats
        )

        return output.model_dump()

    except ValueError as e:
        execution_stats["pipeline_status"] = "error"
        execution_stats["validation_errors"].append(str(e))
        return _build_error_output(execution_stats)

    except Exception as e:
        execution_stats["pipeline_status"] = "error"
        execution_stats["validation_errors"].append(f"Unexpected error: {str(e)}")
        return _build_error_output(execution_stats)


def _build_error_output(stats: Dict[str, Any]) -> Dict[str, Any]:
    """Constructs error response maintaining output schema."""
    return {
        "technical_timeline": {"timeline": []},
        "creative_decisions": {
            "creative_actions": [],
            "mood": "unknown",
            "video_mode": "Business"
        },
        "execution_metadata": stats
    }


def validate_pipeline_output(output: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Post-execution validation of pipeline output.

    Args:
        output: Output dict from run_video_automation_pipeline

    Returns:
        Tuple[bool, List[str]]: (is_valid, list_of_errors)
    """
    errors: List[str] = []

    try:
        PipelineOutput(**output)
    except ValidationError as e:
        errors = [str(err) for err in e.errors()]

    return len(errors) == 0, errors

