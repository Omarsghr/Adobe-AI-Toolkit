import os
import subprocess

def extract_audio(video_path, output_audio_path):
    """Uses FFmpeg to extract high-quality mp3 from video."""
    print(f" Processing: {os.path.basename(video_path)}")

    # Look for ffmpeg.exe in project root or system PATH
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ffmpeg_exe = os.path.join(project_root, "ffmpeg.exe")

    if not os.path.exists(ffmpeg_exe):
        ffmpeg_exe = "ffmpeg"  # Fall back to system PATH
    
    # FFmpeg command: -i (input), -q:a 0 (best quality), -map a (audio only)
    command = [
        ffmpeg_exe, "-i", video_path,
        "-q:a", "0", "-map", "a",
        "-y", output_audio_path # -y forces overwrite
    ]

    try:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        print(f" Audio Extraction Successful: {output_audio_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f" FFmpeg Error: {e}")
        return False

if __name__ == "__main__":
    # Use project root dynamically
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    output_audio = os.path.join(project_root, "temp_audio.mp3")

    # Find ANY video file in the root folder to process
    video_files = [f for f in os.listdir(project_root) if f.endswith(('.mp4', '.mkv', '.mov'))]

    if video_files:
        target_video = os.path.join(project_root, video_files[0])
        extract_audio(target_video, output_audio)
    else:
        print(f" Error: No video files (.mp4, .mkv, .mov) found in {project_root}")