import sqlite3
import os
import json


def initialize_database():
    # تحديد مسار قاعدة البيانات بدقة ف نفس مجلد هاد السكريبت
    db_path = os.path.join(os.path.dirname(__file__), 'project_memory.db')

    # الاتصال بـ SQLite
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("⏳ Initializing all database tables for the pipeline...")

    # 1. الجدول الرئيسي (edit_records)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS edit_records (
            project_id TEXT PRIMARY KEY,
            file_path TEXT NOT NULL,
            ai_zoom_points TEXT,   
            ai_image_paths TEXT,      
            ai_video_paths TEXT,      
            ai_music_paths TEXT,      
            signal_cut_points TEXT, 
            style_metadata TEXT,      
            edit_style TEXT
        )
    ''')

    # 2. جدول الـ transcript (ضروري للـ Director)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transcript (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_text TEXT NOT NULL
        )
    ''')

    # 3. جدول الـ silence_map (ضروري للـ Dead Air و الـ Ducking)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS silence_map (
            start REAL,
            end REAL
        )
    ''')

    # 4. جدول الـ word_timestamps (ضروري للـ Keyword Zoom)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS word_timestamps (
            word TEXT,
            start REAL,
            end REAL
        )
    ''')

    # 5. جدول الـ style_templates الخاص بالتعلم بالقياس (Analogy)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS style_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            style_name TEXT UNIQUE,
            style_type TEXT,
            reference_json TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    print(
        f"✅ Core tables + Style Templates created successfully at: {db_path}")

    # 🌟 زراعة داتا التيست (Seed Data)
    print("🌱 Seeding test data and 10 premium Style Templates...")

    # تنظيف قديم لعدم تكرار الداتا ف التيست
    cursor.execute("DELETE FROM transcript")
    cursor.execute("DELETE FROM silence_map")
    cursor.execute("DELETE FROM word_timestamps")
    cursor.execute("DELETE FROM style_templates")

    # أ. زرع نص الـ Transcript التجريبي
    test_text = (
        "In todays business world, artificial intelligence is changing everything. "
        "We need to focus on key metrics and maximize our growth. "
        "Let us look at the data charts and analyze our strategy for the next quarter."
    )
    cursor.execute(
        "INSERT INTO transcript (id, full_text) VALUES (1, ?)", (test_text,))

    # ب. زرع خريطة الصمت (Silence Map)
    silences = [(0.0, 0.5), (10.2, 12.0), (25.1, 26.5)]
    cursor.executemany(
        "INSERT INTO silence_map (start, end) VALUES (?, ?)", silences)

    # ج. زرع الكلمات المفتاحية بالوقت ديالها لتجربة الـ Zoom
    words_data = [
        ("business", 1.5, 2.0),
        ("intelligence", 3.2, 4.1),
        ("metrics", 8.4, 9.0),
        ("charts", 15.1, 15.8)
    ]
    cursor.executemany(
        "INSERT INTO word_timestamps (word, start, end) VALUES (?, ?, ?)", words_data)

    # د. 🧠 مصفوفة الـ 10 قوالب المرجعية (Educational, Business, Vlog)
    templates_pool = [
        # === 📚 1. EDUCATIONAL CATEGORY (4 القوالب) ===
        {
            "name": "Ali_Abdaal_Premium_Edu",
            "type": "Education",
            "json": {
                "style_metadata": {"pacing": "balanced_educational", "b_roll_density_per_minute": 2, "global_audio": {"bg_music_track": "assets/audio/ambient_study_bg.mp3", "default_music_volume_db": -22, "ducking_on_voice_db": -14}},
                "timeline_data": {
                    "subtitles": {"font": "Montserrat-Bold", "size": 42, "color": "#FFFFFF", "highlight_color": "#00b4e6", "style": "minimal_pop"},
                    "video_track_2_b_roll_images": [{"asset_origin": "generated_image", "generation_prompt": "A highly detailed educational icon, minimalist 3D asset, tech lighting", "start_timestamp": 4.0, "end_timestamp": 9.0, "transition_in": "cross_dissolve"}]
                }
            }
        },
        {
            "name": "Vox_Documentary_Style",
            "type": "Education",
            "json": {
                "style_metadata": {"pacing": "slow_explanatory", "b_roll_density_per_minute": 4, "global_audio": {"bg_music_track": "assets/audio/cinematic_investigative.mp3", "default_music_volume_db": -18, "ducking_on_voice_db": -12}},
                "timeline_data": {
                    "subtitles": {"font": "Georgia-Italic", "size": 36, "color": "#F1C40F", "highlight_color": "#FFFFFF", "style": "lower_third_clean"},
                    "video_track_2_b_roll_images": [{"asset_origin": "generated_image", "generation_prompt": "Vintage textured historical map, ink bleed effect, cinematic archive footage mood", "start_timestamp": 15.0, "end_timestamp": 22.5, "transition_in": "film_fade"}]
                }
            }
        },
        {
            "name": "Kurzgesagt_Infographic",
            "type": "Education",
            "json": {
                "style_metadata": {"pacing": "vibrant_dense", "b_roll_density_per_minute": 5, "global_audio": {"bg_music_track": "assets/audio/playful_synth_science.mp3", "default_music_volume_db": -20, "ducking_on_voice_db": -15}},
                "timeline_data": {
                    "subtitles": {"font": "Fredoka-One", "size": 48, "color": "#FFFFFF", "highlight_color": "#E74C3C", "style": "comic_bubble"},
                    "video_track_2_b_roll_images": [{"asset_origin": "generated_image", "generation_prompt": "Vector art flat illustration of a colorful atom exploding, bright cosmic background", "start_timestamp": 2.0, "end_timestamp": 6.8, "transition_in": "whip_pan"}]
                }
            }
        },
        {
            "name": "Khan_Academy_Minimal",
            "type": "Education",
            "json": {
                "style_metadata": {"pacing": "ultra_slow_lecture", "b_roll_density_per_minute": 1, "global_audio": {"bg_music_track": "None", "default_music_volume_db": -60, "ducking_on_voice_db": 0}},
                "timeline_data": {
                    "subtitles": {"font": "Arial", "size": 32, "color": "#2ECC71", "highlight_color": "#FFFFFF", "style": "basic"},
                    "video_track_2_b_roll_images": [{"asset_origin": "generated_image", "generation_prompt": "Blackboard with clean mathematical formulas written in chalk", "start_timestamp": 10.0, "end_timestamp": 18.0, "transition_in": "cut"}]
                }
            }
        },

        # === 💼 2. BUSINESS CATEGORY (3 القوالب) ===
        {
            "name": "Corporate_Clean_Biz",
            "type": "Business",
            "json": {
                "style_metadata": {"pacing": "professional_fast", "b_roll_density_per_minute": 3, "global_audio": {"bg_music_track": "assets/audio/corporate_uplifting_ambient.mp3", "default_music_volume_db": -24, "ducking_on_voice_db": -16}},
                "timeline_data": {
                    "subtitles": {"font": "Helvetica-Bold", "size": 40, "color": "#FFFFFF", "highlight_color": "#27AE60", "style": "corporate_side_pop"},
                    "video_track_2_b_roll_images": [{"asset_origin": "generated_image", "generation_prompt": "Modern clean corporate office background, glass buildings, ultra-detailed 4k", "start_timestamp": 0.0, "end_timestamp": 4.5, "transition_in": "cross_dissolve"}]
                }
            }
        },
        {
            "name": "Wall_Street_HedgeFund",
            "type": "Business",
            "json": {
                "style_metadata": {"pacing": "aggressive_hyper_fast", "b_roll_density_per_minute": 6, "global_audio": {"bg_music_track": "assets/audio/dark_finance_pulse.mp3", "default_music_volume_db": -18, "ducking_on_voice_db": -10}},
                "timeline_data": {
                    "subtitles": {"font": "Impact", "size": 50, "color": "#00FF00", "highlight_color": "#FFFFFF", "style": "glitch_text"},
                    "video_track_2_b_roll_images": [{"asset_origin": "generated_image", "generation_prompt": "Financial green candlestick stock market charts rising sharply, dark background, 8k resolution", "start_timestamp": 1.0, "end_timestamp": 3.2, "transition_in": "slide_left"}]
                }
            }
        },
        {
            "name": "Startup_Pitch_Deck",
            "type": "Business",
            "json": {
                "style_metadata": {"pacing": "energetic_optimistic", "b_roll_density_per_minute": 4, "global_audio": {"bg_music_track": "assets/audio/indie_rock_corporate.mp3", "default_music_volume_db": -22, "ducking_on_voice_db": -12}},
                "timeline_data": {
                    "subtitles": {"font": "Raleway-Black", "size": 44, "color": "#2C3E50", "highlight_color": "#E67E22", "style": "slide_up"},
                    "video_track_2_b_roll_images": [{"asset_origin": "generated_image", "generation_prompt": "Young diverse entrepreneurs high-fiving in a modern cozy co-working space, soft lighting", "start_timestamp": 5.5, "end_timestamp": 9.0, "transition_in": "cross_dissolve"}]
                }
            }
        },

        # === 🎬 3. VLOG CATEGORY (3 القوالب) ===
        {
            "name": "Casey_Neistat_Vlog",
            "type": "Vlog",
            "json": {
                "style_metadata": {"pacing": "choppy_fast_cuts", "b_roll_density_per_minute": 7, "global_audio": {"bg_music_track": "assets/audio/boom_bap_lofi_hiphop.mp3", "default_music_volume_db": -15, "ducking_on_voice_db": -8}},
                "timeline_data": {
                    "subtitles": {"font": "Courier-Bold", "size": 55, "color": "#FFFF00", "highlight_color": "#000000", "style": "stencil_box"},
                    "video_track_2_b_roll_images": [{"asset_origin": "generated_image", "generation_prompt": "Wide-angle time-lapse of New York City streets, cinematic motion blur, gritty film grain", "start_timestamp": 0.0, "end_timestamp": 2.8, "transition_in": "hard_cut"}]
                }
            }
        },
        {
            "name": "Travel_Cinematic_Vlog",
            "type": "Vlog",
            "json": {
                "style_metadata": {"pacing": "smooth_rhythmic", "b_roll_density_per_minute": 4, "global_audio": {"bg_music_track": "assets/audio/epic_chillstep_travel.mp3", "default_music_volume_db": -20, "ducking_on_voice_db": -14}},
                "timeline_data": {
                    "subtitles": {"font": "Avenir-Light", "size": 38, "color": "#FFFFFF", "highlight_color": "#3498DB", "style": "fade_in_minimal"},
                    "video_track_2_b_roll_images": [{"asset_origin": "generated_image", "generation_prompt": "Breathtaking drone shot of Bali tropical mountains at sunrise, mist, cinematic lighting", "start_timestamp": 8.0, "end_timestamp": 13.4, "transition_in": "cross_dissolve"}]
                }
            }
        },
        {
            "name": "Daily_Lofi_ChillVlog",
            "type": "Vlog",
            "json": {
                "style_metadata": {"pacing": "cozy_slow", "b_roll_density_per_minute": 3, "global_audio": {"bg_music_track": "assets/audio/cozy_lofi_rain.mp3", "default_music_volume_db": -25, "ducking_on_voice_db": -18}},
                "timeline_data": {
                    "subtitles": {"font": "Quicksand-Medium", "size": 36, "color": "#FFC0CB", "highlight_color": "#FFFFFF", "style": "soft_shadow"},
                    "video_track_2_b_roll_images": [{"asset_origin": "generated_image", "generation_prompt": "A steaming cup of coffee next to a rainy window, warm cozy aesthetic, anime bedroom vibe", "start_timestamp": 0.0, "end_timestamp": 5.0, "transition_in": "film_fade"}]
                }
            }
        }
    ]

    # زرع القوالب الـ 10 ف قاعدة البيانات عبر Loop آمنة
    for t in templates_pool:
        cursor.execute("""
            INSERT OR REPLACE INTO style_templates (style_name, style_type, reference_json)
            VALUES (?, ?, ?)
        """, (t["name"], t["type"], json.dumps(t["json"], indent=2)))

    conn.commit()
    conn.close()
    print(f"🎯 DB completely seeded! 10 balanced blueprints are fully loaded into 'style_templates'.")


if __name__ == "__main__":
    initialize_database()
