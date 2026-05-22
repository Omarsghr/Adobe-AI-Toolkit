import os
import sys
import json
import sqlite3
import re
from dotenv import load_dotenv
from openai import OpenAI

# --- 🌟 توحيد المسارات بشكل مطلق ---
ROOT_DIR = "c:/Users/dell/OneDrive/Desktop/.vscode"
DB_PATH = os.path.join(ROOT_DIR, "src/database/project_memory.db")
OUTPUT_JSON = os.path.join(ROOT_DIR, "adobe_screenplay.json")


def initialize_and_verify_db():
    return sqlite3.connect(DB_PATH)


def fetch_style_analogy(chosen_style: str) -> str:
    """🌟 جلب الـ JSON المرجعي من الـ DB بناءً على نوع الستيل المطلوب للتعلم بالقياس"""
    try:
        conn = initialize_and_verify_db()
        cursor = conn.cursor()

        # جلب أحدث قالب متوافق مع الـ style_type (مثلا: Educational أو Business)
        cursor.execute("""
            SELECT reference_json FROM style_templates 
            WHERE style_type = ? 
            ORDER BY timestamp DESC LIMIT 1
        """, (chosen_style,))

        row = cursor.fetchone()
        conn.close()

        if row and row[0]:
            print(
                f"🧠 [Analogy Engine] Successfully loaded reference template for style: '{chosen_style}'")
            return row[0]

    except Exception as e:
        print(
            f"⚠️ [Analogy Engine Warning] Could not fetch style from DB ({e}). Using empty fallback.")

    # Fallback Template في حالة مالقاش الستيل ف الـ DB باش السكريبت ما يوقفش
    return json.dumps({
        "style_metadata": {"pacing": "standard", "b_roll_density_per_minute": 1},
        "timeline_data": {"cuts_and_trims": [], "video_track_2_b_roll_images": []}
    }, indent=2)


def call_local_ollama_director(system_prompt, user_prompt):
    """Placeholder engine to call local Ollama instance on the PC Gamer rig."""
    print("🤖 [Director Mode] Routing request locally to Ollama (llama3.3)...")
    mock_response = {
        "commands": [{"word": "local", "action": "KEYWORD_ZOOM", "style": "smooth"}],
        "image_prompts": [{"prompt": "Local GPU placeholder cinematic image"}],
        "settings": {"music": "local_gamer_rig_ambient_lofi", "lut": "corporate_clean_lut", "font": "Arial-Bold"}
    }
    return mock_response


def clean_llm_json_output(raw_content: str) -> dict:
    """تنظيف وتأمين المخرجات النصية للـ LLM وتحويلها لـ Dictionary حقيقي"""
    if not raw_content:
        return {}
    try:
        # إزالة الـ Markdown Backticks إيلا حطهم الـ Model غلط
        cleaned = raw_content.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return json.loads(cleaned.strip())
    except Exception as e:
        print(f"❌ [JSON Clean Error] Failed to parse LLM response: {e}")
        return {}


def generate_screenplay(video_mode="Business"):
    ai_mode = os.getenv("AI_MODE", "CLOUD").upper()
    print(
        f"\n--- 🎬 AI Video Director Starting | Mode: {ai_mode} | Style: {video_mode} ---")

    # 🌟 Safely dynamic inject the src directory path for architecture modules
    try:
        src_path = os.path.join(ROOT_DIR, "src")
        if src_path not in sys.path:
            sys.path.insert(0, src_path)

        from screenplay.screenplay_architect import ScreenplayArchitect
        from screenplay.subtitle_generator import SubtitleGenerator
        from screenplay.dead_air_detector import DeadAirDetector

        print("✅ Screenplay Advanced Architecture Modules Loaded Successfully!")
    except ImportError as e:
        print(
            f" ❌ Critical Error: Screenplay modules not found ({e}). Stopping pipeline.")
        raise e

    conn = initialize_and_verify_db()
    cursor = conn.cursor()

    modes = {
        "Education": "Focus on clarity. Detect School names, definitions, and technical terms. Action: ZOOM on definitions, GEN_IMAGE for entities.",
        "Vlog": "Focus on personality. Detect emotions, funny moments, and locations. Action: SHAKE for funny parts, WARM_FILTER for stories.",
        "Cinematic": "Focus on visuals. Detect descriptive adjectives (e.g., 'huge', 'dark', 'epic'). Action: SLOW_MO and CINEMATIC_LUT.",
        "Marketing": "Focus on CTA (Call to Action). Detect product names and prices. Action: TEXT_OVERLAY for features.",
        "Business": "Focus on professionalism and clarity. Detect company names, financial terms, and key metrics ($/%). Action: LOWER_THIRD for metrics.",
        "Real_Estate": "Atmosphere focus. Detect room names and luxury terms. Action: WIDE_LENS_CROP, GEN_IMAGE for floorplans.",
        "Social_Media": "Retention focus. Detect hooks and trends. Action: KINETIC_SUBTITLES, FAST_ZOOM, GLITCH_TRANSITIONS."
    }

    selected_instruction = modes.get(video_mode, modes["Business"])

    try:
        # 1. Fetch historical metrics from SQLite
        cursor.execute("SELECT full_text FROM transcript")
        transcript_res = cursor.fetchone()
        cursor.execute("SELECT start, end FROM silence_map")
        silences = cursor.fetchall()

        if not transcript_res or not silences:
            print(
                " ❌ Error: Missing core data in DB. Run transcription and silence maps first.")
            return

        transcript = transcript_res[0]

        # 🌟 جلب القياس (Analogy) الخاص بالـ الستيل المختار
        reference_analogy = fetch_style_analogy(video_mode)

        # 2. Setup the unified Prompts for the AI Director (Injected with Analogy Pattern)
        system_prompt = f"""
        You are an Expert AI Video Director for Adobe Premiere Pro.
        Video Style: {video_mode}.
        Instruction: {selected_instruction}

        You must learn by analogy! Below is a reference example JSON showing the structural DNA, pacing, and metadata style expected for a '{video_mode}' video. 
        Analyze its patterns and mimic the configuration strategy for the new transcript.
        
        --- START REFERENCE ANALOGY ---
        {reference_analogy}
        --- END REFERENCE ANALOGY ---

        CRITICAL EDITING ALIGNMENT: 
        - You MUST extract key moments from the transcript text and generate descriptive image prompts for them.
        - Identify highly descriptive keywords for 'KEYWORD_ZOOM' actions using exact context.
        - Adapt the reference patterns to the new transcript but maintain a clean matching output style.
        - You MUST output ONLY a valid, raw JSON object with this exact schema:
        {{
            "commands": [
                {{"word": "example", "action": "KEYWORD_ZOOM", "style": "cinematic", "sfx": "woosh.mp3"}}
            ],
            "image_prompts": [
                {{"prompt": "A highly detailed professional cinematic 4k image showing the visual concept of the keyword"}}
            ],
            "settings": {{
                "music": "professional_business_lofi_background_music",
                "lut": "corporate_clean_lut",
                "font": "Arial-Bold"
            }}
        }}
        """
        user_prompt = f"Transcript to analyze:\n{transcript}"

        director_screenplay = {}

        # 3. Process LLM based on environment switch (CLOUD vs LOCAL)
        if ai_mode == "LOCAL":
            director_screenplay = call_local_ollama_director(
                system_prompt, user_prompt)
        else:
            nvidia_key = os.getenv("NVIDIA_API_KEY")
            if not nvidia_key:
                print(" ❌ Error: NVIDIA_API_KEY not found in your .env file!")
                return

            print(
                " 🚀 Dispatching query to NVIDIA Cloud [Model: meta/llama-3.3-70b-instruct]...")
            client = OpenAI(
                base_url="[https://integrate.api.nvidia.com/v1](https://integrate.api.nvidia.com/v1)", api_key=nvidia_key)

            response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model="meta/llama-3.3-70b-instruct",
                response_format={"type": "json_object"},
                temperature=0.2
            )
            raw_content = response.choices[0].message.content
            director_screenplay = clean_llm_json_output(raw_content)

        # 4. BUILD KINETIC SCREENPLAY WITH ORIGINAL ARCHITECTURE METRICS
        architect = ScreenplayArchitect(vocal_padding_seconds=0.10, fps=30)

        # Process silence zones and dead air removal
        dead_air_detector = DeadAirDetector(DB_PATH)
        dead_air_zones = dead_air_detector.detect_from_silence_map(silences)

        for start, end in dead_air_zones:
            architect.add_dead_air_removal(start, end)

        # Process keyword zooms if matched in the commands block
        commands_list = director_screenplay.get(
            'commands', []) if director_screenplay else []
        for cmd in commands_list:
            word = cmd.get('word', '')
            action = cmd.get('action', '')
            if action == "KEYWORD_ZOOM" and word:
                cursor.execute(
                    "SELECT start FROM word_timestamps WHERE word LIKE ?", (f"%{word}%",))
                word_match = cursor.fetchone()
                if word_match:
                    word_start = word_match[0]
                    print(
                        f"🔍 [Zoom Effect Linked] Trigger mapped for key term '{word}' at {word_start}s")

        # Process generated image prompts with smooth B-roll timeline layout
        image_prompts = director_screenplay.get(
            'image_prompts', []) if director_screenplay else []
        print(
            f"🎬 [Director Logic] Generated {len(image_prompts)} Smooth Image Asset Triggers!")

        for idx, prompt in enumerate(image_prompts):
            prompt_text = prompt.get('prompt', '') if isinstance(
                prompt, dict) else str(prompt)

            total_time = silences[-1][1] if silences else 30
            start_time = (idx / max(len(image_prompts), 1)) * total_time
            end_time = min(start_time + 4.0, total_time)

            architect.add_b_roll_image(
                generation_prompt=prompt_text,
                start_ts=start_time,
                end_ts=end_time,
                transition_in="cross_dissolve",
                transition_out="fade" if idx < len(
                    image_prompts) - 1 else "none"
            )

        # Incorporate audio background music metrics with active auto-ducking rules
        total_duration = silences[-1][1] if silences else 30
        music_style = director_screenplay.get('settings', {}).get(
            'music', 'ambient professional background') if director_screenplay else 'ambient professional background'

        architect.add_music_bed(
            style_prompt=music_style,
            start_ts=0,
            end_ts=total_duration,
            base_volume_db=-18,
            fade_in_seconds=2.0,
            fade_out_seconds=1.5,
            ducking_attenuation_db=-12
        )

        # 5. Save Final Unified Adobe Export
        architect.save_to_file(OUTPUT_JSON, minify=False)

        print(f" ✅ SUCCESS: Kinetic screenplay file written completely.")
        print(f"    Padding: 0.10s V-Pad | Audio Ducking: Active (-18dB / -12dB Check) | Transitions: Active")
        print(f" 💾 Saved directly to export target: {OUTPUT_JSON}")

    except Exception as e:
        raise e
    finally:
        conn.close()


if __name__ == "__main__":
    load_dotenv(dotenv_path="c:/Users/dell/OneDrive/Desktop/.vscode/.env")
    try:
        chosen_mode = sys.argv[1] if len(sys.argv) > 1 else "Business"
        generate_screenplay(video_mode=chosen_mode)
    except Exception as main_err:
        print(
            f"❌ [CRITICAL RUNTIME ERROR] Director failed at root level: {main_err}")
        sys.exit(1)
