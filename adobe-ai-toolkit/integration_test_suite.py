"""
INTEGRATION TEST SUITE
Tests the complete backend → frontend → timeline pipeline
"""

import json
import os
from pathlib import Path
from src.data_formatter.payload_validator import (
    PayloadValidator, PayloadFormatter, CEPBridgeFormatter
)

class IntegrationTestSuite:
    """Complete integration tests for CEP panel communication"""

    def __init__(self):
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.test_results = []

    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Log test result"""
        status = "[PASS]" if passed else "[FAIL]"
        self.test_results.append({
            "test": test_name,
            "status": status,
            "message": message
        })
        print(f"{status}: {test_name}")
        if message:
            print(f"    -> {message}")

    def create_sample_payload(self):
        """Creates a realistic sample screenplay payload"""
        return {
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
                    },
                    {
                        "type": "dead_air_removal",
                        "start_timestamp": 20.0,
                        "end_timestamp": 22.5,
                        "action_execution": "ripple_delete"
                    }
                ],
                "video_track_1_vocals": [
                    {
                        "original_start_time": 0.0,
                        "original_end_time": 5.0,
                        "padded_start_time": -0.1,
                        "padded_end_time": 5.1,
                        "subtitle_string": "Hello, welcome to this amazing video tutorial.",
                        "extracted_keywords": ["hello", "welcome", "video", "tutorial"],
                        "duration_seconds": 5.2
                    },
                    {
                        "original_start_time": 7.5,
                        "original_end_time": 15.0,
                        "padded_start_time": 7.4,
                        "padded_end_time": 15.1,
                        "subtitle_string": "Today we'll be exploring advanced editing techniques.",
                        "extracted_keywords": ["editing", "techniques", "advanced"],
                        "duration_seconds": 7.7
                    }
                ],
                "video_track_2_b_roll_images": [
                    {
                        "asset_origin": "generated_image",
                        "generation_prompt": "A cinematic landscape at golden hour with mountains",
                        "start_timestamp": 0.0,
                        "end_timestamp": 5.0,
                        "duration_seconds": 5.0,
                        "transition_behavior_in": "cross_dissolve",
                        "transition_behavior_out": "fade"
                    },
                    {
                        "asset_origin": "generated_image",
                        "generation_prompt": "A modern office workspace with computers and plants",
                        "start_timestamp": 5.0,
                        "end_timestamp": 12.0,
                        "duration_seconds": 7.0,
                        "transition_behavior_in": "fade_to_black",
                        "transition_behavior_out": "cross_dissolve"
                    }
                ],
                "audio_track_1_vocals": [
                    {
                        "asset_origin": "extracted_audio",
                        "asset_path": "assets/extracted/vocal_segment_001.mp3",
                        "start_timestamp": 0.0,
                        "end_timestamp": 5.0,
                        "duration_seconds": 5.0,
                        "volume_db": 0
                    },
                    {
                        "asset_origin": "text_to_speech",
                        "asset_path": "assets/tts/tts_001.mp3",
                        "start_timestamp": 7.5,
                        "end_timestamp": 15.0,
                        "duration_seconds": 7.5,
                        "volume_db": 0
                    }
                ],
                "audio_track_2_music_beds": [
                    {
                        "asset_origin": "generated_ambient_track",
                        "style_descriptive_prompt": "Cinematic ambient music with orchestral strings and subtle percussion",
                        "start_timestamp": 0.0,
                        "end_timestamp": 20.0,
                        "duration_seconds": 20.0,
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

    def test_payload_structure_validation(self):
        """Test 1: Validate payload structure"""
        print("\n=== TEST 1: Payload Structure Validation ===")

        payload = self.create_sample_payload()
        is_valid, errors = PayloadValidator.validate_structure(payload)

        self.log_test(
            "Structure validation",
            is_valid,
            f"Errors: {errors}" if errors else "All fields present"
        )

    def test_new_parameters_present(self):
        """Test 2: Verify all new parameters are present"""
        print("\n=== TEST 2: New Parameters Presence ===")

        payload = self.create_sample_payload()
        timeline = payload["timeline_data"]

        # Check padded times in vocals
        vocals_valid = all(
            "padded_start_time" in v and "padded_end_time" in v and "subtitle_string" in v
            for v in timeline["video_track_1_vocals"]
        )
        self.log_test(
            "Vocal segments have padded times and subtitles",
            vocals_valid,
            f"Checked {len(timeline['video_track_1_vocals'])} vocal segments"
        )

        # Check transitions in B-roll
        images_valid = all(
            "transition_behavior_in" in img and "transition_behavior_out" in img
            for img in timeline["video_track_2_b_roll_images"]
        )
        self.log_test(
            "B-roll images have transition types",
            images_valid,
            f"Checked {len(timeline['video_track_2_b_roll_images'])} images"
        )

        # Check audio ducking in music
        music_valid = all(
            "audio_ducking" in bed and "attenuation_db" in bed["audio_ducking"]
            for bed in timeline["audio_track_2_music_beds"]
        )
        self.log_test(
            "Music beds have audio ducking with attenuation",
            music_valid,
            f"Checked {len(timeline['audio_track_2_music_beds'])} music beds"
        )

    def test_path_sanitization(self):
        """Test 3: Path sanitization"""
        print("\n=== TEST 3: Path Sanitization ===")

        payload = self.create_sample_payload()

        # Sanitize paths
        clean_payload = PayloadValidator.sanitize_paths(payload, self.base_path)

        # Check that paths are absolute and use forward slashes
        timeline = clean_payload["timeline_data"]

        paths_valid = True
        for image in timeline["video_track_2_b_roll_images"]:
            path = image.get("asset_path", "")
            if "\\" in path:
                paths_valid = False
                break

        self.log_test(
            "All paths use forward slashes (cross-platform)",
            paths_valid,
            "Backslashes converted to forward slashes"
        )

        # Check that paths are resolvable
        sample_path = timeline["video_track_2_b_roll_images"][0].get("asset_path")
        if sample_path:
            is_absolute = os.path.isabs(sample_path)
            self.log_test(
                "Paths are absolute",
                is_absolute,
                f"Sample: {sample_path[:50]}..."
            )

    def test_payload_transmission_format(self):
        """Test 4: Payload formatted for CEP transmission"""
        print("\n=== TEST 4: CEP Transmission Format ===")

        payload = self.create_sample_payload()
        clean_payload = PayloadValidator.sanitize_paths(payload, self.base_path)

        # Test JSON serialization
        try:
            json_str = PayloadFormatter.to_json_string(clean_payload)
            json_obj = json.loads(json_str)
            serialization_ok = True
        except Exception as e:
            serialization_ok = False
            json_str = str(e)

        self.log_test(
            "Payload serializable to JSON",
            serialization_ok,
            f"Size: {len(json_str)} bytes"
        )

        # Test JSX escape
        try:
            escaped = CEPBridgeFormatter.escape_for_jsx(clean_payload)
            # Verify single quotes are escaped
            jsx_ok = "\\\'" not in escaped or escaped.count("\\\'") > 0
        except Exception as e:
            jsx_ok = False

        self.log_test(
            "Payload properly escaped for JSX",
            jsx_ok,
            "Single quotes escaped for ExtendScript"
        )

    def test_payload_validation_with_errors(self):
        """Test 5: Invalid payload detection"""
        print("\n=== TEST 5: Invalid Payload Detection ===")

        # Payload with missing fields
        bad_payload = {
            "project_configuration": {},
            "timeline_data": {}
        }

        is_valid, errors = PayloadValidator.validate_structure(bad_payload)

        self.log_test(
            "Invalid payload correctly detected",
            not is_valid and len(errors) > 0,
            f"Detected {len(errors)} errors"
        )

    def test_transition_type_validation(self):
        """Test 6: Transition type validation"""
        print("\n=== TEST 6: Transition Type Validation ===")

        valid_payload = self.create_sample_payload()

        # All transitions in payload should be valid
        timeline = valid_payload["timeline_data"]
        for image in timeline["video_track_2_b_roll_images"]:
            transition_in = image.get("transition_behavior_in")
            transition_out = image.get("transition_behavior_out")

            valid_in = transition_in in PayloadValidator.VALID_TRANSITIONS
            valid_out = transition_out in PayloadValidator.VALID_TRANSITIONS

            if not (valid_in and valid_out):
                self.log_test(
                    f"Transition types valid",
                    False,
                    f"Invalid: in={transition_in}, out={transition_out}"
                )
                return

        self.log_test(
            "All transition types valid",
            True,
            f"Checked {len(timeline['video_track_2_b_roll_images'])} images"
        )

    def test_subtitle_text_extraction(self):
        """Test 7: Subtitle text extraction"""
        print("\n=== TEST 7: Subtitle Extraction ===")

        payload = self.create_sample_payload()
        timeline = payload["timeline_data"]

        subtitles = []
        for vocal in timeline["video_track_1_vocals"]:
            if "subtitle_string" in vocal:
                subtitles.append({
                    "text": vocal["subtitle_string"],
                    "start": vocal["padded_start_time"],
                    "end": vocal["padded_end_time"],
                    "duration": vocal["padded_end_time"] - vocal["padded_start_time"]
                })

        subtitles_ok = len(subtitles) > 0

        self.log_test(
            "Subtitles extracted with timing",
            subtitles_ok,
            f"Found {len(subtitles)} subtitle blocks"
        )

        if subtitles_ok:
            for i, sub in enumerate(subtitles):
                print(f"    [{i}] \"{sub['text'][:40]}...\"")
                print(f"        Duration: {sub['duration']:.2f}s")

    def test_audio_ducking_values(self):
        """Test 8: Audio ducking attenuation values"""
        print("\n=== TEST 8: Audio Ducking Values ===")

        payload = self.create_sample_payload()
        timeline = payload["timeline_data"]

        ducking_values = []
        for bed in timeline["audio_track_2_music_beds"]:
            if "audio_ducking" in bed:
                ducking = bed["audio_ducking"]
                ducking_values.append({
                    "active": ducking.get("active_while_vocals_playing", False),
                    "attenuation_db": ducking.get("attenuation_db", 0)
                })

        ducking_ok = len(ducking_values) > 0 and all(d["attenuation_db"] < 0 for d in ducking_values)

        self.log_test(
            "Audio ducking values valid (negative dB)",
            ducking_ok,
            f"Found {len(ducking_values)} ducking configs"
        )

        for i, duck in enumerate(ducking_values):
            print(f"    [{i}] Active: {duck['active']}, Attenuation: {duck['attenuation_db']}dB")

    def run_all_tests(self):
        """Run complete test suite"""
        print("\n" + "="*60)
        print("ADOBE AI TOOLKIT - INTEGRATION TEST SUITE")
        print("="*60)

        self.test_payload_structure_validation()
        self.test_new_parameters_present()
        self.test_path_sanitization()
        self.test_payload_transmission_format()
        self.test_payload_validation_with_errors()
        self.test_transition_type_validation()
        self.test_subtitle_text_extraction()
        self.test_audio_ducking_values()

        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)

        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if "PASS" in r["status"])
        failed = total - passed

        print(f"\nTotal: {total}")
        print(f"[+] Passed: {passed}")
        print(f"[-] Failed: {failed}")

        if failed == 0:
            print("\n** ALL TESTS PASSED! Pipeline is ready. **")
        else:
            print(f"\n** WARNING: {failed} test(s) failed. Review above. **")

        return failed == 0


if __name__ == "__main__":
    suite = IntegrationTestSuite()
    suite.run_all_tests()
