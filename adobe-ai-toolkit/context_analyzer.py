import os
import json
import sqlite3  # This is required to execute the SQL commands
import requests

# Set database path dynamically
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'project_memory.db')


def analyze_video_context():
    print("\n🧠 [Context Analyzer] Starting linguistic analysis & video DNA extraction...")

    # Ensure the DB file exists
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at: {DB_PATH}. Please ensure it exists.")
        return

    # Connect to the DB
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Fetch the transcript
        cursor.execute("SELECT full_text FROM transcript LIMIT 1")
        row = cursor.fetchone()

        if not row or not row[0]:
            print("⚠️ [Warning] No transcript found in DB. Aborting.")
            return

        transcript_text = row[0]
        print(f"📄 [Data Found] Analyzing text stream...")

        # Prepare the prompt for the Local LLM (Ollama)
        system_prompt = (
            "You are an expert media analyst. Classify the core context of a video. "
            "You MUST categorize the video into exactly ONE of these styles: 'Education', 'Business', or 'Vlog'. "
            "Return ONLY a strictly valid JSON object."
        )

        user_prompt = f"""
        Analyze the transcript below and output this exact JSON structure:
        {{
          "main_topic": "1-sentence summary",
          "target_audience": "Who is this for",
          "tone": "Detected tone",
          "edit_style": "Must be either 'Education', 'Business', or 'Vlog'"
        }}

        Transcript: "{transcript_text}"
        """

        # Call Ollama
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.3",
                "prompt": f"{system_prompt}\n\n{user_prompt}",
                "stream": False,
                "format": "json"
            },
            timeout=60
        )

        if response.status_code != 200:
            raise Exception(f"Ollama returned HTTP status {response.status_code}")

        # Parse and save the result
        raw_response = response.json().get('response', '{}').strip()
        analysis_res = json.loads(raw_response)

        detected_style = analysis_res.get("edit_style", "Education")

        # Save to DB (This table will appear in your PyCharm Database Tool)
        cursor.execute("""
            INSERT OR REPLACE INTO edit_records (project_id, file_path, style_metadata, edit_style)
            VALUES (?, ?, ?, ?)
        """, (
            "current_project",
            "incoming_jobs/active_sequence.mp4",
            json.dumps(analysis_res),
            detected_style
        ))

        conn.commit()
        print(f"✅ [Success] Context analyzed and saved for style: {detected_style}")

    except Exception as e:
        print(f"❌ [Pipeline Crash] {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    analyze_video_context()