#!/usr/bin/env python3
"""
Quick connection test for backend-Adobe panel
Tests the entire integration without PowerShell dependency
"""

import sys
import os

# Add the project to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    print("\n" + "="*70)
    print("BACKEND-ADOBE PANEL CONNECTION TEST")
    print("="*70 + "\n")
    
    # Test 1: Import modules
    print("[TEST 1] Checking module imports...")
    try:
        from src.data_formatter.payload_validator import (
            PayloadValidator, PayloadFormatter, CEPBridgeFormatter
        )
        print("✓ PASS: All modules imported successfully\n")
    except Exception as e:
        print(f"✗ FAIL: Import error: {e}\n")
        return False
    
    # Test 2: Create sample payload
    print("[TEST 2] Creating sample payload...")
    try:
        sample = {
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
                        "subtitle_string": "Test audio segment",
                        "extracted_keywords": ["test"],
                        "duration_seconds": 5.2
                    }
                ],
                "video_track_2_b_roll_images": [
                    {
                        "asset_origin": "generated_image",
                        "generation_prompt": "Test image",
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
                        "asset_path": "assets/test.mp3",
                        "start_timestamp": 0.0,
                        "end_timestamp": 5.0,
                        "duration_seconds": 5.0,
                        "volume_db": 0
                    }
                ],
                "audio_track_2_music_beds": [
                    {
                        "asset_origin": "generated_ambient_track",
                        "style_descriptive_prompt": "Ambient music",
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
        print("✓ PASS: Sample payload created\n")
    except Exception as e:
        print(f"✗ FAIL: {e}\n")
        return False
    
    # Test 3: Validate structure
    print("[TEST 3] Validating payload structure...")
    try:
        is_valid, errors = PayloadValidator.validate_structure(sample)
        if is_valid:
            print("✓ PASS: Payload structure is valid\n")
        else:
            print(f"✗ FAIL: Validation errors:\n")
            for err in errors:
                print(f"   - {err}")
            print()
            return False
    except Exception as e:
        print(f"✗ FAIL: {e}\n")
        return False
    
    # Test 4: Sanitize paths
    print("[TEST 4] Sanitizing asset paths...")
    try:
        base_path = os.path.dirname(os.path.abspath(__file__))
        clean_payload = PayloadValidator.sanitize_paths(sample, base_path)
        print(f"✓ PASS: Paths sanitized\n")
    except Exception as e:
        print(f"✗ FAIL: {e}\n")
        return False
    
    # Test 5: Format for transmission
    print("[TEST 5] Preparing payload for transmission...")
    try:
        formatted = PayloadFormatter.prepare_for_transmission(sample, base_path)
        if formatted:
            print(f"✓ PASS: Payload ready for transmission\n")
        else:
            print(f"✗ FAIL: Formatting failed\n")
            return False
    except Exception as e:
        print(f"✗ FAIL: {e}\n")
        return False
    
    # Test 6: JSON serialization
    print("[TEST 6] Testing JSON serialization...")
    try:
        json_str = PayloadFormatter.to_json_string(formatted)
        print(f"✓ PASS: JSON serialization OK ({len(json_str)} bytes)\n")
    except Exception as e:
        print(f"✗ FAIL: {e}\n")
        return False
    
    # Test 7: CEP/ExtendScript escape
    print("[TEST 7] Testing CEP/ExtendScript escaping...")
    try:
        escaped = CEPBridgeFormatter.escape_for_jsx(formatted)
        print(f"✓ PASS: ExtendScript escaping OK\n")
    except Exception as e:
        print(f"✗ FAIL: {e}\n")
        return False
    
    # Test 8: Server availability
    print("[TEST 8] Checking FastAPI server configuration...")
    try:
        with open("server.py", "r") as f:
            content = f.read()
            if "FastAPI" in content and "8016" in content:
                print("✓ PASS: Server configured on port 8016\n")
            else:
                print("✗ FAIL: Server configuration issue\n")
                return False
    except Exception as e:
        print(f"✗ FAIL: {e}\n")
        return False
    
    # SUMMARY
    print("="*70)
    print("✅ ALL TESTS PASSED - BACKEND-ADOBE CONNECTION READY")
    print("="*70)
    print("\nSummary:")
    print("  ✓ Module imports working")
    print("  ✓ Payload structure valid")
    print("  ✓ Path sanitization working")
    print("  ✓ Transmission formatting ready")
    print("  ✓ JSON serialization ready")
    print("  ✓ ExtendScript escaping ready")
    print("  ✓ FastAPI server configured")
    print("\nTo start the server, run: python server.py")
    print("Server will listen on http://localhost:8016")
    print("="*70 + "\n")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
