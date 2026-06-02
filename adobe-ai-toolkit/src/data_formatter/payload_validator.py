"""
PAYLOAD VALIDATOR & PATH RESOLVER
Ensures backend-generated assets are correctly formatted and paths are clean
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class PayloadValidator:
    """Validates screenplay payload before sending to frontend"""

    REQUIRED_CONFIG_FIELDS = [
        "target_sequence_fps",
        "global_vocal_padding_seconds",
    ]

    REQUIRED_TIMELINE_FIELDS = [
        "cuts_and_trims",
        "video_track_1_vocals",
        "video_track_2_b_roll_images",
        "audio_track_1_vocals",
        "audio_track_2_music_beds"
    ]

    VALID_TRANSITIONS = [
        "cross_dissolve", "fade_to_black", "dip_to_white", "fade", "none"
    ]

    VALID_ASSET_ORIGINS = [
        "generated_image",
        "generated_ambient_track",
        "text_to_speech",
        "extracted_audio",
        "dead_air_removal"
    ]

    @staticmethod
    def validate_structure(payload: Dict) -> Tuple[bool, List[str]]:
        """
        Validates the complete payload structure
        Returns: (is_valid, list_of_errors)
        """
        errors = []

        # Check top-level structure
        if "project_configuration" not in payload:
            errors.append("Missing: project_configuration")
        else:
            for field in PayloadValidator.REQUIRED_CONFIG_FIELDS:
                if field not in payload["project_configuration"]:
                    errors.append(f"Missing config field: {field}")

        if "timeline_data" not in payload:
            errors.append("Missing: timeline_data")
        else:
            timeline = payload["timeline_data"]
            for field in PayloadValidator.REQUIRED_TIMELINE_FIELDS:
                if field not in timeline:
                    errors.append(f"Missing timeline field: {field}")

        # Validate vocal segments
        if "timeline_data" in payload:
            vocals = payload["timeline_data"].get("video_track_1_vocals", [])
            for i, vocal in enumerate(vocals):
                if "padded_start_time" not in vocal:
                    errors.append(f"Vocal segment {i}: missing padded_start_time")
                if "padded_end_time" not in vocal:
                    errors.append(f"Vocal segment {i}: missing padded_end_time")
                if "subtitle_string" not in vocal:
                    errors.append(f"Vocal segment {i}: missing subtitle_string")

            # Validate B-roll images
            images = payload["timeline_data"].get("video_track_2_b_roll_images", [])
            for i, image in enumerate(images):
                if "transition_behavior_in" not in image:
                    errors.append(f"B-roll image {i}: missing transition_behavior_in")
                else:
                    if image["transition_behavior_in"] not in PayloadValidator.VALID_TRANSITIONS:
                        errors.append(f"B-roll image {i}: invalid transition_behavior_in")

                if "transition_behavior_out" not in image:
                    errors.append(f"B-roll image {i}: missing transition_behavior_out")

            # Validate music beds
            music_beds = payload["timeline_data"].get("audio_track_2_music_beds", [])
            for i, bed in enumerate(music_beds):
                if "audio_ducking" not in bed:
                    errors.append(f"Music bed {i}: missing audio_ducking")
                else:
                    ducking = bed["audio_ducking"]
                    if "attenuation_db" not in ducking:
                        errors.append(f"Music bed {i}: ducking missing attenuation_db")

        return len(errors) == 0, errors

    @staticmethod
    def sanitize_paths(payload: Dict, base_path: str) -> Dict:
        """
        Sanitizes and validates all asset file paths
        Returns the payload with clean, verified paths
        """
        if "timeline_data" not in payload:
            return payload

        timeline = payload["timeline_data"]

        # Process B-roll images
        for image in timeline.get("video_track_2_b_roll_images", []):
            if "asset_path" in image:
                image["asset_path"] = PayloadValidator._clean_path(image["asset_path"], base_path)
            else:
                # Generate path from asset_origin
                generated_path = PayloadValidator._generate_asset_path(
                    image.get("asset_origin", "generated_image"),
                    base_path
                )
                if generated_path is not None:
                    image["asset_path"] = generated_path

        # Process music beds
        for bed in timeline.get("audio_track_2_music_beds", []):
            if "asset_path" in bed:
                bed["asset_path"] = PayloadValidator._clean_path(bed["asset_path"], base_path)
            else:
                generated_path = PayloadValidator._generate_asset_path(
                    bed.get("asset_origin", "generated_ambient_track"),
                    base_path
                )
                if generated_path is not None:
                    bed["asset_path"] = generated_path

        # Process vocal audio
        for vocal in timeline.get("audio_track_1_vocals", []):
            if "asset_path" in vocal:
                vocal["asset_path"] = PayloadValidator._clean_path(vocal["asset_path"], base_path)

        return payload

    @staticmethod
    def _clean_path(file_path: str, base_path: str) -> str:
        """
        Cleans a file path:
        - Converts backslashes to forward slashes
        - Ensures it's within base_path
        - Resolves relative paths
        """
        # Normalize separators
        file_path = file_path.replace("\\", "/")

        # If relative, make absolute within base_path
        if not os.path.isabs(file_path):
            file_path = os.path.join(base_path, file_path).replace("\\", "/")

        # Resolve and normalize
        resolved = str(Path(file_path).resolve()).replace("\\", "/")

        return resolved

    @staticmethod
    def _generate_asset_path(asset_origin: str, base_path: str) -> Optional[str]:
        """
        Generates a proper asset path based on asset_origin type
        """
        asset_map = {
            "generated_image": "assets/ai_images/",
            "generated_ambient_track": "assets/ai_music/",
            "text_to_speech": "assets/tts/",
            "extracted_audio": "assets/extracted/",
            "dead_air_removal": None
        }

        relative = asset_map.get(asset_origin, "assets/")
        if relative is None:
            return None

        full_path = os.path.join(base_path, relative).replace("\\", "/")
        return full_path

    @staticmethod
    def verify_asset_existence(payload: Dict) -> Tuple[bool, List[str]]:
        """
        Checks if all referenced asset files exist on disk
        Returns: (all_exist, list_of_missing_files)
        """
        missing = []

        if "timeline_data" not in payload:
            return True, []

        timeline = payload["timeline_data"]

        # Check B-roll images
        for image in timeline.get("video_track_2_b_roll_images", []):
            if "asset_path" in image and image["asset_path"]:
                if not os.path.exists(image["asset_path"]):
                    missing.append(f"Image not found: {image['asset_path']}")

        # Check music beds
        for bed in timeline.get("audio_track_2_music_beds", []):
            if "asset_path" in bed and bed["asset_path"]:
                if not os.path.exists(bed["asset_path"]):
                    missing.append(f"Audio not found: {bed['asset_path']}")

        # Check vocal audio
        for vocal in timeline.get("audio_track_1_vocals", []):
            if "asset_path" in vocal and vocal["asset_path"]:
                if not os.path.exists(vocal["asset_path"]):
                    missing.append(f"Vocal audio not found: {vocal['asset_path']}")

        return len(missing) == 0, missing


class PayloadFormatter:
    """Formats payload for clean transmission to CEP panel"""

    @staticmethod
    def prepare_for_transmission(payload: Dict, asset_base_path: str) -> Dict:
        """
        Prepares payload for sending to the frontend:
        1. Validates structure
        2. Sanitizes paths
        3. Verifies assets
        4. Removes internal fields
        """
        # Validate
        is_valid, errors = PayloadValidator.validate_structure(payload)
        if not is_valid:
            print(f" Payload validation errors:\n" + "\n".join(errors))
            return None

        # Sanitize paths
        clean_payload = PayloadValidator.sanitize_paths(payload, asset_base_path)

        # Verify assets
        assets_exist, missing = PayloadValidator.verify_asset_existence(clean_payload)
        if not assets_exist:
            print(f" Missing asset files:\n" + "\n".join(missing))

        # Add metadata for frontend
        clean_payload["_metadata"] = {
            "version": "1.0",
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "asset_base_path": asset_base_path,
            "validation_status": "passed" if is_valid else "warnings"
        }

        return clean_payload

    @staticmethod
    def to_json_string(payload: Dict, minify: bool = False) -> str:
        """Converts payload to JSON string for transmission"""
        if minify:
            return json.dumps(payload, separators=(',', ':'))
        return json.dumps(payload, indent=2)


class CEPBridgeFormatter:
    """Formats payload specifically for CEP/ExtendScript communication"""

    @staticmethod
    def escape_for_jsx(payload: Dict) -> str:
        """
        Escapes JSON string for safe transmission to ExtendScript
        ExtendScript requires single quotes to be escaped
        """
        json_str = json.dumps(payload)
        # Escape single quotes for JSX string literals
        escaped = json_str.replace("'", "\\'")
        return escaped

    @staticmethod
    def create_jsx_payload_code(payload: Dict) -> str:
        """
        Creates complete JSX code that defines the payload variable
        This can be directly eval'd from the HTML panel
        """
        escaped = CEPBridgeFormatter.escape_for_jsx(payload)
        jsx_code = f"""
        var screenplayPayload = JSON.parse('{escaped}');
        applyScreenplayToTimeline(screenplayPayload);
        """
        return jsx_code


# Example usage and integration point
if __name__ == "__main__":
    # Sample payload for testing
    sample_payload = {
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
                    "padded_start_time": -0.1,
                    "padded_end_time": 5.1,
                    "subtitle_string": "Hello, this is the opening segment",
                    "extracted_keywords": ["hello", "opening"],
                    "duration_seconds": 5.2
                }
            ],
            "video_track_2_b_roll_images": [
                {
                    "asset_origin": "generated_image",
                    "generation_prompt": "A cinematic landscape",
                    "start_timestamp": 0.0,
                    "end_timestamp": 5.0,
                    "duration_seconds": 5.0,
                    "transition_behavior_in": "cross_dissolve",
                    "transition_behavior_out": "fade"
                }
            ],
            "audio_track_1_vocals": [
                {
                    "asset_origin": "extracted_audio",
                    "asset_path": "assets/extracted/vocal_1.mp3",
                    "start_timestamp": 0.0,
                    "end_timestamp": 5.0,
                    "duration_seconds": 5.0,
                    "volume_db": 0
                }
            ],
            "audio_track_2_music_beds": [
                {
                    "asset_origin": "generated_ambient_track",
                    "style_descriptive_prompt": "Ambient background music",
                    "start_timestamp": 0.0,
                    "end_timestamp": 10.0,
                    "duration_seconds": 10.0,
                    "base_volume_db": -18,
                    "audio_ducking": {
                        "active_while_vocals_playing": True,
                        "attenuation_db": -12
                    },
                    "fade_in_seconds": 2.0,
                    "fade_out_seconds": 1.5
                }
            ]
        }
    }

    # Test validation
    is_valid, errors = PayloadValidator.validate_structure(sample_payload)
    print(f"Validation: {' PASS' if is_valid else ' FAIL'}")
    if errors:
        for error in errors:
            print(f"  - {error}")

    # Test transmission prep
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    prepared = PayloadFormatter.prepare_for_transmission(
        sample_payload,
        project_root
    )

    if prepared:
        print("\n Payload ready for transmission")
        print(f"Timeline contains:")
        print(f"  - {len(prepared['timeline_data']['cuts_and_trims'])} dead air zones")
        print(f"  - {len(prepared['timeline_data']['video_track_1_vocals'])} vocal segments")
        print(f"  - {len(prepared['timeline_data']['video_track_2_b_roll_images'])} B-roll images")
        print(f"  - {len(prepared['timeline_data']['audio_track_2_music_beds'])} music beds")
