import subprocess
import sys
import os

def main():
    print(" INITIALIZING ADOBE-AI-TOOLKIT MASTER PIPELINE")
    print("=" * 60)

    # Paths to sub-scripts
    base = "Adobe-AI-Toolkit/github/src/transcription"
    ai_logic = "Adobe-AI-Toolkit/github/src/ai_logic"

    # Step 1: Extract
    print("\n--- [1/5] EXTRACTING AUDIO ---")
    subprocess.run([sys.executable, f"{base}/audio_processor.py"])

    # Step 2: Transcribe with word-level timestamps
    print("\n--- [2/5] AI TRANSCRIPTION WITH WORD TIMESTAMPS ---")
    subprocess.run([sys.executable, f"{base}/transcription_manager.py"])

    # Step 3: Analyze silence & dead air
    print("\n--- [3/5] AUDIO INTELLIGENCE (SILENCE & DEAD AIR) ---")
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    result = subprocess.run([
        sys.executable, "-c",
        f"""
import os, sys
sys.path.insert(0, 'src/signal_analysis')
sys.path.insert(0, 'src/screenplay')
from signal_processor import analyze_silence
from dead_air_detector import DeadAirDetector
import sqlite3

root_dir = r"{root_dir}"
db_path = os.path.join(root_dir, "project_memory.db")
audio_file = os.path.join(root_dir, "temp_audio.mp3")

if os.path.exists(audio_file):
    analyze_silence(audio_file, db_path)

    # Load transcript with word timestamps
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT full_text FROM transcript LIMIT 1")
    transcript = cursor.fetchone()[0] if cursor.fetchone() else ""
    conn.close()

    detector = DeadAirDetector(db_path)
    print(" Dead air detection initialized")
else:
    print(f" Audio file not found at {{audio_file}}")
"""
    ])

    # Step 4: Generate Screenplay with Kinetic Architecture
    print("\n--- [4/5] KINETIC SCREENPLAY GENERATION ---")
    subprocess.run([sys.executable, f"{ai_logic}/keyword_director.py"])

    # Step 5: Generate Images with Optimized Prompts
    print("\n--- [5/5] VISUAL ASSET GENERATION (OPTIMIZED) ---")
    result = subprocess.run([
        sys.executable, "-c",
        """
import sys
sys.path.insert(0, 'src/ai_logic')
from visualist_generator import generate_and_store_free
generate_and_store_free()
"""
    ])

    print("\n" + "=" * 60)
    print(" PIPELINE COMPLETE")
    print(" DATABASE: project_memory.db")
    print(" SCREENPLAY: adobe_screenplay.json (NEW KINEMATIC FORMAT)")
    print(" IMAGES: assets/ai_images/")
    print("=" * 60)

if __name__ == "__main__":
    main()