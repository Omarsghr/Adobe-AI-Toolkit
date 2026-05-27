import os
import subprocess
import sys

# Configuration - Use the directory where this script is located
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_EXE = sys.executable


def run_script(script_path, args=None):
    """Helper to run a sub-script with optional arguments and dynamic PYTHONPATH."""
    print(f"\n▶️ --- Running: {os.path.basename(script_path)} ---")

    if not os.path.exists(script_path):
        print(f"❌ [ERROR] Script not found at: {script_path}")
        return False

    command = [PYTHON_EXE, script_path]
    if args:
        command.extend(args)

    try:
        # 🌟 تأمين الـ Imports لداخل: كنضيفو مجلد السكريبت للـ PYTHONPATH مؤقتاً
        script_dir = os.path.dirname(script_path)
        env = os.environ.copy()
        env["PYTHONPATH"] = script_dir + os.pathsep + env.get("PYTHONPATH", "")

        # تشغيل السكريبت مع الحفاظ على الـ Working Directory الرئيسي للمشروع
        result = subprocess.run(
            command,
            cwd=ROOT_DIR,
            env=env,
            capture_output=False,  # كنخليو الـ Logs تبان ديريكت ف الـ Terminal ديال السيرفر
            check=True            # كيطيح Exception إيلا السكريبت لداخل رجع خطأ
        )
        return True
    except subprocess.CalledProcessError as e:
        print(
            f"❌ [ERROR] Script {os.path.basename(script_path)} failed with return code {e.returncode}. Stopping pipeline.")
        return False
    except Exception as e:
        print(
            f"⚠️ [ERROR] Unexpected failure running {os.path.basename(script_path)}: {e}")
        return False


def run_master_pipeline(target_audio=None, video_mode="Business"):
    """
    The main engine. Updates the workflow to include transcription 
    and ensures correct sequential data flow.

    🌟 مـحـدّث لـقـبـول الـ video_mode وتـمـريـره لـلـمـديـر الـفـنّـي (Few-Shot Analogy).
    """
    print(
        f"\n🎬 === STARTING AUTO-EDITOR AI MASTER GLUE [Mode: {video_mode}] === 🎬\n")

    # 1. THE EYE (Signal Analysis / Silence Mapping)
    # 📝 كيطحن الـ Waves ويسيف الـ Silence ف الـ DB
    eye_script = os.path.join(
        ROOT_DIR, "src", "signal_analysis", "signal_processor.py")
    eye_args = [target_audio] if target_audio else []
    if not run_script(eye_script, eye_args):
        return None

    # 2. THE EAR (AI Transcription)
    # 🌟 كياخد الـ Audio وصيفطو لـ Groq ويصنع الـ Transcript ف الـ DB
    ear_script = os.path.join(
        ROOT_DIR, "src", "transcription", "transcription_manager.py")
    ear_args = [target_audio] if target_audio else []
    if not run_script(ear_script, ear_args):
        return None

    # 3. THE BRAIN (Director Logic with Few-Shot Analogy)
    # 📝 كياخد الـ DB ويـجـبـد الـ Template المرجعي بـنـاءً عـلـى الـ video_mode ويصنع adobe_screenplay.json
    brain_script = os.path.join(
        ROOT_DIR, "src", "ai_logic", "keyword_director.py")

    # 🌟 هـنـا كـانـحـقـنـو الـ video_mode كـ وسـيـط تـنـفـيـذي لـلـسـكـريـبـت الـفـرعـي
    # الـ Director غـادي يـقـرا هـاد الـ argument بـ sys.argv أو نـعـدلـوه يـشـوف الـ بـورت مـبـاشـرة
    # بـمـا أن الـ Director لـديـنـا عـبـارة عـن دالـة، فـالأفـضـل نـمـرروه كـ اركـيـومـنـت لـلـسـكـريـبـت
    brain_args = [video_mode]
    if not run_script(brain_script, brain_args):
        return None

    # 4. THE VISUALIST (Final Integration Test / Script Application)
    visualist_script = os.path.join(
        ROOT_DIR, "src", "ai_logic", "visualist_generator.py")
    if not run_script(visualist_script):
        return None

    # تشيك أخير على وجود الملف قبل النجاح
    result_json_path = os.path.join(ROOT_DIR, "adobe_screenplay.json")
    if os.path.exists(result_json_path):
        print("\n" + "="*50)
        print("🎉 [SUCCESS] MASTER PIPELINE COMPLETE WITH ANALOGY STRATEGY")
        print(f"📄 Output: {result_json_path}")
        print("="*50 + "\n")
        return result_json_path
    else:
        print("❌ [ERROR] Pipeline finished but adobe_screenplay.json is missing.")
        return None


if __name__ == "__main__":
    # إيلا شـغّـلـتـي الـ مـاسـتـر يـدويّـاً مـن الـ Terminal للـتـجـربـة:
    # تـقـدر تـكـتـب مـثـلاً: python main.py inputs/test.mp3 Education
    target = sys.argv[1] if len(sys.argv) > 1 else None
    mode = sys.argv[2] if len(sys.argv) > 2 else "Business"

    run_master_pipeline(target_audio=target, video_mode=mode)
