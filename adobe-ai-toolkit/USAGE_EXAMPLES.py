"""
PRACTICAL USAGE EXAMPLES

Real-world scenarios for using the new Adobe-AI-Toolkit features
"""

# ============================================================================
# EXAMPLE 1: COMPLETE PIPELINE EXECUTION
# ============================================================================

def example_complete_pipeline():
    """
    Demonstrates the complete pipeline from audio to Premiere Pro JSON.
    """
    import os
    import json
    from src.screenplay import (
        ScreenplayArchitect,
        DeadAirDetector,
        SubtitleGenerator,
        AudioMusicGenerator
    )
    from src.transcription.groq_clients import transcribe_with_groq
    from src.signal_analysis.signal_processor import analyze_silence
    from src.ai_logic.visualist_generator import PromptOptimizer

    # 1. Transcribe audio with word timestamps
    audio_file = "project.mp3"
    transcript_json = "map.json"
    transcript_text = transcribe_with_groq(audio_file, transcript_json)

    # 2. Load word timestamps from transcription
    with open(transcript_json) as f:
        transcript_data = json.load(f)
        word_timestamps = transcript_data.get("word_timestamps", [])

    # 3. Detect dead air
    db_path = "project_memory.db"
    silence_analyzer_result = analyze_silence(audio_file, db_path)

    dead_air_detector = DeadAirDetector(db_path)
    silence_zones = dead_air_detector.detect_from_silence_map([
        (0.5, 1.0), (5.0, 5.5), (10.0, 10.8)  # Example zones
    ])
    filler_zones = dead_air_detector.detect_filler_words(
        transcript_text, word_timestamps
    )

    # 4. Generate subtitles
    subtitle_gen = SubtitleGenerator(words_per_subtitle=6)
    subtitles = subtitle_gen.generate_from_word_timestamps(word_timestamps)
    subtitle_gen.save_srt("output_subtitles.srt")

    # 5. Build screenplay with ScreenplayArchitect
    architect = ScreenplayArchitect(vocal_padding_seconds=0.10, fps=30)

    # Add dead air removal zones
    for start, end in dead_air_detector.get_all_dead_air_zones():
        architect.add_dead_air_removal(start, end)

    # Add vocal segments from subtitles
    for subtitle in subtitles:
        architect.add_vocal_segment(
            start_time=subtitle["start_time"],
            end_time=subtitle["end_time"],
            subtitle_text=subtitle["subtitle_text"],
            keywords=subtitle["extracted_keywords"]
        )

    # Add B-roll images with transitions
    images = ["Professional office", "Team collaboration", "Success metrics"]
    total_duration = subtitles[-1]["end_time"] if subtitles else 30
    image_duration = total_duration / len(images)

    for idx, img_prompt in enumerate(images):
        start = idx * image_duration
        end = start + image_duration
        architect.add_b_roll_image(
            generation_prompt=img_prompt,
            start_ts=start,
            end_ts=end,
            transition_in="cross_dissolve",
            transition_out="fade" if idx < len(images) - 1 else "none"
        )

    # Add background music with ducking
    architect.add_music_bed(
        style_prompt="Cinematic ambient background suitable for business video",
        start_ts=0,
        end_ts=total_duration,
        base_volume_db=-18,
        fade_in_seconds=2.0,
        fade_out_seconds=1.5,
        ducking_attenuation_db=-12
    )

    # 6. Export screenplay
    architect.save_to_file("adobe_screenplay.json", minify=False)
    print("✅ Complete pipeline executed!")


# ============================================================================
# EXAMPLE 2: OPTIMIZED IMAGE GENERATION FOR COST TIER
# ============================================================================

def example_optimized_image_generation():
    """
    Shows how to optimize image prompts for $0.004 cost tier.
    """
    from src.ai_logic.visualist_generator import (
        PromptOptimizer,
        generate_and_store_free
    )
    import json

    # Initialize optimizer
    optimizer = PromptOptimizer(cost_tier_usd=0.004)

    # Examples of prompt optimization
    raw_prompts = [
        "A very beautiful and extremely detailed professional office space with lots of very nice windows showing the absolutely stunning cityscape outside",
        "Kind of a dark, sort of minimalist workspace with really nice wooden desks and like modern lighting fixtures",
        "An absolutely amazing team collaboration scene with very colorful sticky notes and really enthusiastic people working together"
    ]

    print("📝 PROMPT OPTIMIZATION EXAMPLES:\n")
    for idx, raw in enumerate(raw_prompts, 1):
        optimized = optimizer.optimize_prompt(raw)
        print(f"{idx}. ORIGINAL ({len(raw)} chars):")
        print(f"   {raw}\n")
        print(f"   OPTIMIZED ({len(optimized)} chars):")
        print(f"   {optimized}\n")
        print()

    # Generate images with optimized prompts
    screenplay = {
        "image_prompts": [
            {"keyword": "office_space", "prompt": raw_prompts[0]},
            {"keyword": "workspace", "prompt": raw_prompts[1]},
            {"keyword": "team_work", "prompt": raw_prompts[2]}
        ]
    }

    generate_and_store_free(screenplay, use_optimized_prompts=True)


# ============================================================================
# EXAMPLE 3: DEAD AIR DETECTION AND REPORTING
# ============================================================================

def example_dead_air_detection():
    """
    Detailed example of dead air detection with reporting.
    """
    from src.screenplay import DeadAirDetector

    # Example word timestamps from Whisper transcription
    word_timestamps = [
        {"word": "Hello", "start": 0.0, "end": 0.5},
        {"word": "everyone", "start": 0.5, "end": 1.0},
        {"word": "um", "start": 1.0, "end": 1.3},  # Filler word
        {"word": "today", "start": 1.3, "end": 1.8},
        {"word": "we're", "start": 1.8, "end": 2.2},
        {"word": "going", "start": 2.2, "end": 2.6},
        {"word": "to", "start": 2.6, "end": 2.9},
        {"word": "talk", "start": 2.9, "end": 3.3},
        # Long silence here (3.3s to 5.0s)
        {"word": "like", "start": 5.0, "end": 5.2},  # Filler word
        {"word": "about", "start": 5.2, "end": 5.7},
        {"word": "productivity", "start": 5.7, "end": 6.4}
        # Trailing silence from 6.4s to 8.0s
    ]

    # Silence intervals from librosa analysis
    silence_intervals = [
        (3.3, 5.0),    # Long pause between sentences
        (6.4, 8.0)     # Trailing silence
    ]

    # Create detector
    detector = DeadAirDetector("project_memory.db")

    # Process silence intervals
    print("🔍 DETECTING DEAD AIR ZONES:\n")

    dead_air_from_silence = detector.detect_from_silence_map(silence_intervals)
    print(f"✓ Detected {len(dead_air_from_silence)} silence zones:")
    for start, end in dead_air_from_silence:
        print(f"  - {start:.1f}s to {end:.1f}s ({end-start:.1f}s duration)")

    # Detect filler words
    filler_zones = detector.detect_filler_words("", word_timestamps)
    print(f"\n✓ Detected {len(filler_zones)} filler word zones:")
    for start, end in filler_zones:
        # Find matching word
        for word_data in word_timestamps:
            if word_data["start"] == start:
                print(f"  - '{word_data['word']}' at {start:.1f}s to {end:.1f}s")
                break

    # Detect trailing silence
    trailing = detector.detect_trailing_silence(word_timestamps, 8.0)
    print(f"\n✓ Detected {len(trailing)} trailing silence zone(s):")
    for start, end in trailing:
        print(f"  - {start:.1f}s to {end:.1f}s ({end-start:.1f}s duration)")

    # Generate report
    report = detector.create_deletion_report()
    print(f"\n📊 DELETION REPORT:")
    print(f"Total zones: {report['total_zones_detected']}")
    print(f"Total removal duration: {report['total_deletion_duration_seconds']}s")


# ============================================================================
# EXAMPLE 4: SUBTITLE GENERATION WITH KEYWORD EXTRACTION
# ============================================================================

def example_subtitle_generation():
    """
    Creates subtitles with automatic keyword extraction.
    """
    from src.screenplay import SubtitleGenerator

    # Word timestamps from transcription
    word_timestamps = [
        {"word": "Machine", "start": 0.0, "end": 0.4},
        {"word": "learning", "start": 0.4, "end": 0.8},
        {"word": "is", "start": 0.8, "end": 0.95},
        {"word": "transforming", "start": 0.95, "end": 1.5},
        {"word": "how", "start": 1.5, "end": 1.7},
        {"word": "we", "start": 1.7, "end": 1.85},
        {"word": "build", "start": 1.85, "end": 2.2},
        {"word": "software", "start": 2.2, "end": 2.8},
        # ... pause ...
        {"word": "Today", "start": 4.0, "end": 4.3},
        {"word": "we'll", "start": 4.3, "end": 4.6},
        {"word": "explore", "start": 4.6, "end": 5.0},
        {"word": "practical", "start": 5.0, "end": 5.5},
        {"word": "applications", "start": 5.5, "end": 6.2}
    ]

    # Generate subtitles
    generator = SubtitleGenerator(words_per_subtitle=6, max_line_width=42)
    subtitles = generator.generate_from_word_timestamps(word_timestamps)

    print("📝 GENERATED SUBTITLES:\n")
    for idx, subtitle in enumerate(subtitles, 1):
        print(f"Block {idx}: {subtitle['start_time']:.1f}s → {subtitle['end_time']:.1f}s")
        print(f"Text: {subtitle['subtitle_text']}")
        print(f"Keywords: {', '.join(subtitle['extracted_keywords'])}")
        print()

    # Export formats
    generator.save_srt("subtitles.srt")
    generator.save_vtt("subtitles.vtt")

    # Generate report
    report = generator.create_subtitle_report()
    print(f"📊 SUBTITLE REPORT:")
    print(f"Total subtitles: {report['total_subtitles']}")
    print(f"Total duration: {report['total_duration_seconds']}s")
    print(f"Avg words per subtitle: {report['average_words_per_subtitle']}")
    print(f"All keywords: {', '.join(report['unique_keywords'])}")


# ============================================================================
# EXAMPLE 5: MUSIC GENERATION WITH DUCKING
# ============================================================================

def example_music_generation():
    """
    Generates background music and configures audio ducking.
    """
    from src.screenplay import AudioMusicGenerator, ScreenplayArchitect

    # Initialize music generator
    music_gen = AudioMusicGenerator(output_dir="assets/ai_music")

    print("🎵 GENERATING BACKGROUND MUSIC:\n")

    # Generate ambient track (free tier - requires HF token)
    try:
        asset_path, duration = music_gen.generate_ambient_free(
            style_prompt="Professional corporate background with subtle strings and piano",
            duration_seconds=30.0,
            genre="corporate_ambient"
        )
        print(f"✓ Generated: {asset_path}")
        print(f"  Duration: {duration}s")
    except Exception as e:
        print(f"⚠️ Generation failed (may need HF token): {e}")
        # Fallback - use placeholder
        asset_path = "assets/ai_music/ambient_corporate_ambient_30s.mp3"

    # Create screenplay with music bed and ducking
    architect = ScreenplayArchitect()

    # Add music with automatic ducking
    architect.add_music_bed(
        style_prompt="Professional corporate background with subtle strings and piano",
        start_ts=0.0,
        end_ts=30.0,
        base_volume_db=-18,
        fade_in_seconds=2.0,
        fade_out_seconds=1.5,
        ducking_attenuation_db=-12  # Reduce by 12dB during vocals
    )

    # Add vocal segment (music will auto-duck)
    architect.add_vocal_segment(
        start_time=5.0,
        end_time=15.0,
        subtitle_text="Important message during video",
        keywords=["important", "message"]
    )

    # Export
    screenplay = architect.export_json()
    music_config = screenplay["timeline_data"]["audio_track_2_music_beds"][0]

    print("\n🎼 MUSIC BED CONFIGURATION:")
    print(f"Base volume: {music_config['base_volume_db']}dB")
    print(f"Ducking active: {music_config['audio_ducking']['active_while_vocals_playing']}")
    print(f"Ducking attenuation: {music_config['audio_ducking']['attenuation_db']}dB")
    print(f"Fade in: {music_config['fade_in_seconds']}s")
    print(f"Fade out: {music_config['fade_out_seconds']}s")


# ============================================================================
# EXAMPLE 6: CEP PANEL INTEGRATION - Parsing Screenplay
# ============================================================================

def example_cep_panel_parsing():
    """
    Shows how a CEP panel in Premiere Pro would parse the screenplay JSON.
    This is pseudocode for the JSX context.
    """

    pseudo_jsx_code = """
    // Example CEP Panel Code for Adobe Premiere Pro

    // 1. Load screenplay JSON
    var screenplayPath = "/path/to/adobe_screenplay.json";
    var screenplay = JSON.parse(readFile(screenplayPath));

    // 2. Get active sequence
    var sequence = app.project.activeSequence;
    var videoTrack = sequence.videoTracks[0];
    var audioTrack = sequence.audioTracks[0];

    // 3. Process dead air removal zones
    screenplay.timeline_data.cuts_and_trims.forEach(function(cut) {
        if (cut.type === "dead_air_removal") {
            var startTime = new Time(cut.start_timestamp);
            var endTime = new Time(cut.end_timestamp);
            // Ripple delete from startTime to endTime
            sequence.rippleDelete(startTime, endTime);
        }
    });

    // 4. Process vocal segments with padding
    screenplay.timeline_data.video_track_1_vocals.forEach(function(vocal) {
        var startTime = new Time(vocal.padded_start_time);
        var endTime = new Time(vocal.padded_end_time);

        // Create video clip reference
        var clip = sequence.createAdjustmentClip(startTime, endTime - startTime);

        // Add subtitle track
        var subtitleTrack = sequence.createSubtitleTrack();
        subtitleTrack.addSubtitle(startTime, endTime, vocal.subtitle_string);
    });

    // 5. Process B-roll images with transitions
    screenplay.timeline_data.video_track_2_b_roll_images.forEach(function(image) {
        var startTime = new Time(image.start_timestamp);
        var duration = new Time(image.duration_seconds);

        // Apply transition in
        applyTransition(image.transition_behavior_in, startTime);

        // Generate or import image
        generateImage(image.generation_prompt, image.asset_origin);

        // Apply transition out
        applyTransition(image.transition_behavior_out, startTime + duration);
    });

    // 6. Process audio ducking
    screenplay.timeline_data.audio_track_2_music_beds.forEach(function(music) {
        var clip = audioTrack.insertMediaClip(music.asset_origin);
        clip.volume = music.base_volume_db;

        // Apply fade in/out
        applyFade(clip, "in", music.fade_in_seconds);
        applyFade(clip, "out", music.fade_out_seconds);

        // Configure ducking during vocal segments
        if (music.audio_ducking.active_while_vocals_playing) {
            screenplay.timeline_data.video_track_1_vocals.forEach(function(vocal) {
                applyDucking(
                    clip,
                    vocal.padded_start_time,
                    vocal.padded_end_time,
                    music.audio_ducking.attenuation_db
                );
            });
        }
    });

    alert("✓ Screenplay applied to sequence!");
    """

    print("📝 EXAMPLE CEP PANEL INTEGRATION CODE:\n")
    print(pseudo_jsx_code)


# ============================================================================
# RUN ALL EXAMPLES
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("ADOBE-AI-TOOLKIT: PRACTICAL USAGE EXAMPLES")
    print("=" * 70)

    examples = [
        ("Complete Pipeline", example_complete_pipeline),
        ("Optimized Image Generation", example_optimized_image_generation),
        ("Dead Air Detection", example_dead_air_detection),
        ("Subtitle Generation", example_subtitle_generation),
        ("Music Generation", example_music_generation),
        ("CEP Panel Integration", example_cep_panel_parsing)
    ]

    print("\nAvailable examples:")
    for idx, (name, _) in enumerate(examples, 1):
        print(f"{idx}. {name}")

    # Uncomment to run specific examples:
    # example_dead_air_detection()
    # example_subtitle_generation()
    # example_music_generation()
    # example_cep_panel_parsing()
