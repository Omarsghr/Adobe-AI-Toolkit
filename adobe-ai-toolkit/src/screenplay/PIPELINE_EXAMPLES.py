"""
Example Usage: Multi-Agent Video Automation Pipeline

This demonstrates how to use the production-ready screenplay module pipeline
to process raw video data through Agent 1 (Technical Trimmer) and Agent 2
(Creative Director) to generate cinematic production-ready output.
"""

from src.screenplay import run_video_automation_pipeline, validate_pipeline_output
import json


# Example 1: Basic Pipeline Execution
def example_basic_pipeline():
    """Demonstrates minimal required input for pipeline execution."""

    # Minimal transcript data: Must include word_timestamps and video_duration
    transcript_data = {
        "word_timestamps": [
            {"word": "Hello", "start": 0.0, "end": 0.5, "confidence": 0.98},
            {"word": "this", "start": 0.5, "end": 0.7, "confidence": 0.99},
            {"word": "is", "start": 0.7, "end": 0.9, "confidence": 0.98},
            {"word": "a", "start": 0.9, "end": 1.0, "confidence": 0.97},
            {"word": "test", "start": 1.0, "end": 1.3, "confidence": 0.99},
        ],
        "video_duration": 10.0,
        "silence_intervals": [(5.0, 6.0), (8.0, 8.5)],
    }

    # Execute pipeline with mood and video mode
    output = run_video_automation_pipeline(
        transcript_data=transcript_data,
        mood="inspiring",
        video_mode="Business",
        intensity_multiplier=1.0
    )

    print("Pipeline Status:", output["execution_metadata"]["pipeline_status"])
    print("Total Actions Generated:", output["execution_metadata"]["total_actions_generated"])
    print("Technical Actions:", output["execution_metadata"]["technical_actions_count"])
    print("Creative Actions:", output["execution_metadata"]["creative_actions_count"])

    return output


# Example 2: Complex Real-World Scenario
def example_complex_scenario():
    """Demonstrates comprehensive pipeline with full metadata."""

    # Realistic transcript with many words
    word_timestamps = [
        {"word": word, "start": i * 0.3, "end": i * 0.3 + 0.25, "confidence": 0.95 + (i % 5) * 0.01}
        for i, word in enumerate([
            "Welcome", "to", "our", "comprehensive", "video", "editing",
            "platform", "today", "we", "will", "explore", "the", "amazing",
            "capabilities", "of", "AI", "driven", "screenplay", "generation"
        ])
    ]

    transcript_data = {
        "word_timestamps": word_timestamps,
        "video_duration": 30.0,
        "silence_intervals": [
            (5.5, 6.2),   # ~700ms silence
            (12.0, 12.8), # ~800ms silence
            (18.5, 19.1), # ~600ms silence
            (25.0, 26.5), # ~1.5s silence
        ],
        "full_transcript": " ".join([w["word"] for w in word_timestamps])
    }

    # Test different moods
    moods = ["inspiring", "dramatic", "calm", "energetic"]
    results = {}

    for mood in moods:
        output = run_video_automation_pipeline(
            transcript_data=transcript_data,
            mood=mood,
            video_mode="Educational",
            intensity_multiplier=1.2
        )

        results[mood] = {
            "status": output["execution_metadata"]["pipeline_status"],
            "total_actions": output["execution_metadata"]["total_actions_generated"],
            "dead_air_zones": output["execution_metadata"]["dead_air_zones_removed"],
            "subtitles": output["execution_metadata"]["subtitles_generated"],
            "creative_actions": output["execution_metadata"]["creative_actions_count"]
        }

    return results


# Example 3: Pipeline Output Validation
def example_validation():
    """Demonstrates post-execution validation of pipeline output."""

    transcript_data = {
        "word_timestamps": [
            {"word": "Quick", "start": 0.0, "end": 0.3, "confidence": 0.99},
            {"word": "test", "start": 0.3, "end": 0.6, "confidence": 0.98},
        ],
        "video_duration": 5.0,
    }

    output = run_video_automation_pipeline(
        transcript_data=transcript_data,
        mood="calm"
    )

    is_valid, errors = validate_pipeline_output(output)

    print(f"Output Valid: {is_valid}")
    if errors:
        print("Validation Errors:", errors)
    else:
        print("All validations passed!")

    return is_valid


# Example 4: Error Handling - Invalid Input
def example_error_handling():
    """Demonstrates graceful error handling with invalid inputs."""

    # Missing video_duration
    invalid_transcript = {
        "word_timestamps": [
            {"word": "test", "start": 0.0, "end": 0.5, "confidence": 0.99}
        ]
        # Missing: "video_duration"
    }

    output = run_video_automation_pipeline(
        transcript_data=invalid_transcript,
        mood="inspiring",
        enable_validation=True  # Strict validation
    )

    status = output["execution_metadata"]["pipeline_status"]
    print(f"Pipeline Status: {status}")
    print(f"Errors: {output['execution_metadata']['validation_errors']}")

    return status


# Example 5: Production JSON Output
def example_json_export():
    """Demonstrates exporting pipeline output as production-ready JSON."""

    transcript_data = {
        "word_timestamps": [
            {"word": "Production", "start": 0.0, "end": 0.5, "confidence": 0.99},
            {"word": "ready", "start": 0.5, "end": 0.9, "confidence": 0.98},
            {"word": "output", "start": 0.9, "end": 1.3, "confidence": 0.99},
        ],
        "video_duration": 8.0,
        "silence_intervals": [(4.0, 5.0)]
    }

    output = run_video_automation_pipeline(
        transcript_data=transcript_data,
        mood="professional" if "professional" in ["inspiring", "dramatic", "calm", "energetic"] else "inspiring",
        video_mode="Business"
    )

    # Export as minified JSON for API transmission
    json_str = json.dumps(output, indent=2)
    minified_json = json.dumps(output, separators=(',', ':'))

    print(f"Formatted JSON Size: {len(json_str)} bytes")
    print(f"Minified JSON Size: {len(minified_json)} bytes")
    print(f"Compression Ratio: {(1 - len(minified_json)/len(json_str)) * 100:.1f}%")

    # Save to file
    with open("pipeline_output.json", "w") as f:
        json.dump(output, f, indent=2)

    print("Output saved to pipeline_output.json")

    return output


# Example 6: Advanced Usage - Custom Intensity Scaling
def example_intensity_scaling():
    """Demonstrates how intensity scaling affects creative decisions."""

    base_data = {
        "word_timestamps": [
            {"word": "test", "start": float(i) * 0.5, "end": float(i) * 0.5 + 0.4}
            for i in range(10)
        ],
        "video_duration": 6.0,
    }

    intensity_levels = [0.5, 1.0, 1.5, 2.0]
    results = {}

    for intensity in intensity_levels:
        output = run_video_automation_pipeline(
            transcript_data=base_data,
            mood="dramatic",
            intensity_multiplier=intensity
        )

        # Extract zoom levels from creative actions
        zoom_actions = [
            a for a in output["creative_decisions"]["creative_actions"]
            if a.get("action") == "APPLY_ZOOM_PUNCH_IN"
        ]

        if zoom_actions:
            avg_zoom = sum(a["zoom_level"] for a in zoom_actions) / len(zoom_actions)
            results[intensity] = {
                "zoom_count": len(zoom_actions),
                "average_zoom": avg_zoom
            }

    print("Intensity Scaling Results:")
    for intensity, result in results.items():
        print(f"  Intensity {intensity}: {result['zoom_count']} zooms, avg: {result['average_zoom']:.2f}x")

    return results


if __name__ == "__main__":
    print("=" * 70)
    print("Multi-Agent Video Automation Pipeline - Examples")
    print("=" * 70)

    print("\n[Example 1] Basic Pipeline Execution")
    print("-" * 70)
    ex1 = example_basic_pipeline()

    print("\n[Example 2] Complex Scenario with Multiple Moods")
    print("-" * 70)
    ex2 = example_complex_scenario()
    for mood, data in ex2.items():
        print(f"{mood:12} → Status: {data['status']:8} | Total: {data['total_actions']:2} actions | Dead Air: {data['dead_air_zones']} | Subtitles: {data['subtitles']} | Creative: {data['creative_actions']}")

    print("\n[Example 3] Output Validation")
    print("-" * 70)
    ex3 = example_validation()

    print("\n[Example 4] Error Handling")
    print("-" * 70)
    ex4 = example_error_handling()

    print("\n[Example 5] JSON Export for Production")
    print("-" * 70)
    ex5 = example_json_export()

    print("\n[Example 6] Intensity Scaling Impact")
    print("-" * 70)
    ex6 = example_intensity_scaling()

    print("\n" + "=" * 70)
    print("All examples completed successfully!")
    print("=" * 70)

