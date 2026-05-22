import json
from typing import List, Dict, Tuple, Optional

class ScreenplayArchitect:
    """
    Converts raw director commands and timing data into a cinematic Screenplay JSON
    with mandatory vocal padding, transition properties, and audio ducking.
    """

    def __init__(self, vocal_padding_seconds: float = 0.10, fps: int = 30):
        self.vocal_padding = vocal_padding_seconds
        self.fps = fps
        self.timeline_data = {
            "project_configuration": {
                "target_sequence_fps": fps,
                "global_vocal_padding_seconds": vocal_padding_seconds,
                "default_image_cost_tier_usd": 0.004
            },
            "timeline_data": {
                "cuts_and_trims": [],
                "video_track_1_vocals": [],
                "video_track_2_b_roll_images": [],
                "audio_track_1_vocals": [],
                "audio_track_2_music_beds": []
            }
        }

    def add_dead_air_removal(self, start_ts: float, end_ts: float) -> None:
        """Registers a dead-air zone for ripple deletion."""
        self.timeline_data["timeline_data"]["cuts_and_trims"].append({
            "type": "dead_air_removal",
            "start_timestamp": round(start_ts, 3),
            "end_timestamp": round(end_ts, 3),
            "action_execution": "ripple_delete"
        })

    def add_vocal_segment(
        self,
        start_time: float,
        end_time: float,
        subtitle_text: str,
        keywords: List[str]
    ) -> None:
        """Adds a vocal segment with mandatory 0.10s padding on both ends."""
        padded_start = max(0.0, start_time - self.vocal_padding)
        padded_end = end_time + self.vocal_padding

        self.timeline_data["timeline_data"]["video_track_1_vocals"].append({
            "original_start_time": round(start_time, 3),
            "original_end_time": round(end_time, 3),
            "padded_start_time": round(padded_start, 3),
            "padded_end_time": round(padded_end, 3),
            "subtitle_string": subtitle_text,
            "extracted_keywords": keywords,
            "duration_seconds": round(padded_end - padded_start, 3)
        })

    def add_b_roll_image(
        self,
        generation_prompt: str,
        start_ts: float,
        end_ts: float,
        transition_in: str = "cross_dissolve",
        transition_out: str = "none",
        asset_origin: str = "generated_image"
    ) -> None:
        """Adds a B-roll image with explicit transition properties."""
        valid_transitions = ["cross_dissolve", "fade_to_black", "dip_to_white", "fade", "none"]
        transition_in = transition_in if transition_in in valid_transitions else "cross_dissolve"
        transition_out = transition_out if transition_out in valid_transitions else "none"

        self.timeline_data["timeline_data"]["video_track_2_b_roll_images"].append({
            "asset_origin": asset_origin,
            "generation_prompt": generation_prompt,
            "start_timestamp": round(start_ts, 3),
            "end_timestamp": round(end_ts, 3),
            "duration_seconds": round(end_ts - start_ts, 3),
            "transition_behavior_in": transition_in,
            "transition_behavior_out": transition_out
        })

    def add_music_bed(
        self,
        style_prompt: str,
        start_ts: float,
        end_ts: float,
        base_volume_db: float = -18,
        fade_in_seconds: float = 2.0,
        fade_out_seconds: float = 1.5,
        ducking_attenuation_db: float = -12
    ) -> None:
        """Adds a music bed with ducking during vocal segments."""
        self.timeline_data["timeline_data"]["audio_track_2_music_beds"].append({
            "asset_origin": "generated_ambient_track",
            "style_descriptive_prompt": style_prompt,
            "start_timestamp": round(start_ts, 3),
            "end_timestamp": round(end_ts, 3),
            "duration_seconds": round(end_ts - start_ts, 3),
            "base_volume_db": base_volume_db,
            "audio_ducking": {
                "active_while_vocals_playing": True,
                "attenuation_db": ducking_attenuation_db
            },
            "fade_in_seconds": fade_in_seconds,
            "fade_out_seconds": fade_out_seconds
        })

    def add_vocal_track_element(
        self,
        start_ts: float,
        end_ts: float,
        asset_path: str,
        volume_db: float = 0
    ) -> None:
        """Adds a vocal audio track element (TTS or extracted)."""
        self.timeline_data["timeline_data"]["audio_track_1_vocals"].append({
            "asset_origin": "text_to_speech" if "tts" in asset_path.lower() else "extracted_audio",
            "asset_path": asset_path,
            "start_timestamp": round(start_ts, 3),
            "end_timestamp": round(end_ts, 3),
            "duration_seconds": round(end_ts - start_ts, 3),
            "volume_db": volume_db
        })

    def export_json(self) -> Dict:
        """Returns the final screenplay JSON."""
        return self.timeline_data

    def export_json_string(self, minify: bool = False) -> str:
        """Exports as JSON string, optionally minified."""
        if minify:
            return json.dumps(self.timeline_data, separators=(',', ':'))
        return json.dumps(self.timeline_data, indent=2)

    def save_to_file(self, filepath: str, minify: bool = False) -> None:
        """Saves the screenplay to a JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.export_json_string(minify=minify))
        print(f" Screenplay saved to: {filepath}")
