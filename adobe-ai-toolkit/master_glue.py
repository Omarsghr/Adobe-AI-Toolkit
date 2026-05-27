import subprocess
import os
import sys


def find_file(filename, search_path):
    for root, dirs, files in os.walk(search_path):
        if filename in files:
            return os.path.join(root, filename)
    return None


def main():
    # 🌟 1. قراءة الـ Arguments اللي جايين من السيرفر (server.py)
    # sys.argv[1] غايكون هو الـ target_audio و sys.argv[2] هو الـ video_mode
    target_audio = sys.argv[1] if len(sys.argv) > 1 else None
    video_mode = sys.argv[2] if len(sys.argv) > 2 else "Business"

    print(
        f"\n🎬 === STARTING MASTER GLUE PIPELINE [Mode: {video_mode}] === 🎬\n")

    python_exe = sys.executable
    current_dir = os.getcwd()

    # 🔄 الترتيب المنطقي للـ Pipeline مع تحديد الـ Arguments لكل خطوة
    pipeline_files = [
        # ("اسم الخطوة", "اسم السكريبت", [الـ Arguments الخاصة بيه])
        ("AUDIO EXTRACTION", "audio_processor.py",
         [target_audio] if target_audio else []),
        ("SILENCE ANALYSIS", "signal_processor.py",
         [target_audio] if target_audio else []),
        ("AI TRANSCRIPTION", "transcription_manager.py",
         [target_audio] if target_audio else []),
        # 🌟 خطوة الـ Director دابا غاتاخد الـ video_mode كـ Argument باش تجبد الـ Analogy من الـ DB
        ("DIRECTOR LOGIC", "keyword_director.py", [video_mode])
    ]

    print("🚀 ADOBE-AI-TOOLKIT: AUTO-LOCATING PIPELINE COMPONENTS")

    for step_name, filename, args in pipeline_files:
        print(f"\n▶️ Running Step: {step_name} ({filename})...")
        file_path = find_file(filename, current_dir)

        if file_path:
            print(f"✅ Auto-Located at: {file_path}")
            try:
                script_dir = os.path.dirname(file_path)
                env = os.environ.copy()
                env["PYTHONPATH"] = script_dir + \
                    os.pathsep + env.get("PYTHONPATH", "")

                # 🌟 بناء الأمر الكامل: بايثون + مسار السكريبت + الـ Arguments (بحال الـ video_mode)
                command = [python_exe, file_path]
                if args:
                    command.extend(args)

                result = subprocess.run(
                    command,
                    cwd=current_dir,  # يبقى شايف الفولدر الرئيسي للمشروع
                    env=env,          # تمرير الـ environment المعدلة
                    check=True
                )
                print(f"✨ {step_name} Completed Successfully!")
            except subprocess.CalledProcessError as e:
                print(
                    f"❌ CRITICAL ERROR in {step_name}: Script returned non-zero exit code. Stopping.")
                break
            except Exception as e:
                print(f"⚠️ Unexpected Error in {step_name}: {e}")
                break
        else:
            print(
                f"❌ FAILED: Could not find {filename} anywhere inside {current_dir}")
            break


if __name__ == "__main__":
    main()
