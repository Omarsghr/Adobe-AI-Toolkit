import os
import sqlite3
import librosa
import numpy as np
import subprocess
import sys
import imageio_ffmpeg  # 👈 ضفنا هادي هنا


def extract_audio_from_video(video_path, output_audio_path):
    """Extract audio from video using FFmpeg."""
    print(f"[VIDEO] Extracting audio from: {os.path.basename(video_path)}")

    # 1. جلب المسار الحقيقي والمضمون ديال ffmpeg.exe اللي منزل ف الـ venv ديريكت
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    command = [
        ffmpeg_exe,
        "-y",               # Overwrite
        "-i", video_path,   # الفيديو المدخل
        "-vn",              # إلغاء الفيديو
        "-acodec", "libmp3lame",  # 👈 بدلنا هادي لـ libmp3lame باش توافق الـ MP3
        "-ar", "16000",     # 16kHz
        "-ac", "1",         # Mono
        output_audio_path   # المسار اللي كيسالي بـ .mp3
    ]

    try:
        # 3. تشغيل الـ Process
        # إستعمال creationflags كيمع ظهور نافذة الـ CMD كحلة ف كل مرة كيتشغل ffmpeg ف ويندوز
        startupinfo = None
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            startupinfo=startupinfo,
            check=True  # كيطيح الخطأ إيلا ffmpeg فشل ف الاستخراج
        )
        print(f"✅ [VIDEO] Audio extracted successfully: {output_audio_path}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ [ERROR] FFmpeg failed: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ [ERROR] Audio extraction failed: {str(e)}")
        return False


def analyze_silence(audio_path, db_path):
    print(
        f"[ANALYSIS] Analyzing audio waves for: {os.path.basename(audio_path)}")

    try:
        # Load audio file
        y, sr = librosa.load(audio_path, sr=None)

        # Detect non-silent intervals (top_db=30 is usually good for voice)
        intervals = librosa.effects.split(y, top_db=30)

        # Calculate silent segments
        silences = []
        last_end = 0
        for start, end in intervals:
            if start > last_end:
                silences.append((last_end / sr, start / sr))
            last_end = end

        # Add final silence if it exists
        duration = librosa.get_duration(y=y, sr=sr)
        if last_end / sr < duration:
            silences.append((last_end / sr, duration))

        # Save to the CENTRAL Database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # CRITICAL: Create table if missing, but DO NOT drop 'transcript'
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS silence_map (start REAL, end REAL)")
        # Clear old silence data only
        cursor.execute("DELETE FROM silence_map")

        for start, end in silences:
            cursor.execute(
                "INSERT INTO silence_map (start, end) VALUES (?, ?)", (start, end))

        conn.commit()
        conn.close()

        print(f"[OK] Found {len(silences)} silent segments.")
        print(f"[DB] Silence map saved to: {db_path}")
        return True

    except Exception as e:
        print(f"[ERROR] Silence Analysis Error: {e}")
        return False


if __name__ == "__main__":
    root_dir = os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))
    db_path = os.path.join(root_dir, "project_memory.db")
    temp_audio = os.path.join(root_dir, "temp_audio.mp3")

    success = False

    # Check if file path was provided as argument
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        print(f"[INPUT] Processing file from argument: {input_file}")

        # If it's a video file, extract audio first
        if input_file.lower().endswith(('.mp4', '.mkv', '.mov', '.avi', '.webm')):
            if extract_audio_from_video(input_file, temp_audio):
                success = analyze_silence(temp_audio, db_path)
            else:
                print(f"[ERROR] Failed to extract audio from {input_file}")
        elif input_file.lower().endswith(('.mp3', '.wav', '.aac', '.m4a')):
            # It's already audio
            success = analyze_silence(input_file, db_path)
        else:
            print(f"[ERROR] Unsupported file format: {input_file}")
    else:
        # Fall back to looking for temp_audio files
        audio_candidates = [temp_audio, os.path.join(
            root_dir, "temp_audio.wav")]
        found_audio = None
        for audio_path in audio_candidates:
            if os.path.exists(audio_path):
                found_audio = audio_path
                break

        if found_audio:
            success = analyze_silence(found_audio, db_path)
        else:
            print(
                f"[ERROR] Could not find audio file (tried: {', '.join(audio_candidates)})")

    sys.exit(0 if success else 1)
