import os
import subprocess
import sys

# تحديد المسار الرئيسي للمشروع (الفولدر الأب)
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_EXE = sys.executable


def run_script(script_path, args=None):
    """دالة مساعدة لتشغيل السكريبتات الفرعية مع تمرير الـ الـ Arguments وتأمين الـ PYTHONPATH"""
    print(f"\n▶️ --- Running Component: {os.path.basename(script_path)} ---")

    if not os.path.exists(script_path):
        print(f"❌ [ERROR] Script not found at: {script_path}")
        return False

    command = [PYTHON_EXE, script_path]
    if args:
        command.extend(args)

    try:
        # تأمين الـ Imports لداخل عبر الـ PYTHONPATH مؤقتاً
        script_dir = os.path.dirname(script_path)
        env = os.environ.copy()
        env["PYTHONPATH"] = script_dir + os.pathsep + env.get("PYTHONPATH", "")

        # تشغيل السكريبت
        subprocess.run(
            command,
            cwd=ROOT_DIR,
            env=env,
            capture_output=False,  # الـ Logs كتبان مباشرة ف الـ Terminal د السيرفر
            check=True             # كيطيح Exception إيلا السكريبت لداخل رجع خطأ
        )
        return True
    except subprocess.CalledProcessError as e:
        print(
            f"❌ [ERROR] {os.path.basename(script_path)} failed with code {e.returncode}. Pipeline halted.")
        return False
    except Exception as e:
        print(
            f"⚠️ [ERROR] Unexpected crash during execution of {os.path.basename(script_path)}: {e}")
        return False


def run_master_pipeline(target_audio=None, video_mode="Business"):
    """
    The Master Engine: Orchestrates the pipeline components in order.
    """
    print(f"\n🎬 === STARTING AI AUTOPILOT PIPELINE [Mode: {video_mode}] === 🎬\n")

    # Define all component paths in a dictionary to keep it clean
    components = {
        "Audio": os.path.join(ROOT_DIR, "src", "audio_processing", "audio_processor.py"),
        "Signal": os.path.join(ROOT_DIR, "src", "signal_analysis", "signal_processor.py"),
        "Transcription": os.path.join(ROOT_DIR, "src", "transcription", "transcription_manager.py"),
        "Director": os.path.join(ROOT_DIR, "src", "ai_logic", "keyword_director.py"),
        "Visualist": os.path.join(ROOT_DIR, "src", "ai_logic", "visualist_generator.py")
    }

    # 1. AUDIO EXTRACTION
    if os.path.exists(components["Audio"]):
        if not run_script(components["Audio"], [target_audio] if target_audio else None):
            return None

    # 2. THE EYE (Signal Analysis)
    if not run_script(components["Signal"], [target_audio] if target_audio else None):
        return None

    # 3. THE EAR (Transcription)
    if not run_script(components["Transcription"], [target_audio] if target_audio else None):
        return None

    # 4. THE BRAIN (Director Logic)
    # Passing the video_mode here
    if not run_script(components["Director"], [video_mode]):
        return None

    # 5. THE VISUALIST
    if os.path.exists(components["Visualist"]):
        if not run_script(components["Visualist"]):
            return None

    # Final Verification
    result_json_path = os.path.join(ROOT_DIR, "adobe_screenplay.json")
    if os.path.exists(result_json_path):
        print("\n" + "=" * 60)
        print("🎉 [SUCCESS] MAIN PIPELINE COMPLETE")
        print("=" * 60 + "\n")
        return result_json_path

    return None

if __name__ == "__main__":
    # كود التشغيل اليدوي من الـ Terminal للـ Debugging
    target = sys.argv[1] if len(sys.argv) > 1 else None
    mode = sys.argv[2] if len(sys.argv) > 2 else "Business"

    run_master_pipeline(target_audio=target, video_mode=mode)
