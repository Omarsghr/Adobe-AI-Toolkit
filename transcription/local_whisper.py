import os
import json
from groq import Groq
from dotenv import load_dotenv

# Load keys from .env
load_dotenv()

# Define the bank of 15 keys
API_KEYS = [os.getenv(f"GROQ_KEY_{i}") for i in range(1, 16) if os.getenv(f"GROQ_KEY_{i}")]

def transcribe_with_groq(audio_file_path, output_json="map.json"):
    """
    High-speed transcription using 15 Groq keys to bypass rate limits.
    """
    if not API_KEYS:
        print(" Error: No API keys (GROQ_KEY_1 to GROQ_KEY_15) found in .env")
        return None

    if not os.path.exists(audio_file_path):
        print(f" Error: Audio file not found at {audio_file_path}")
        return None

    print(f" Uploading to Groq Cloud: {os.path.basename(audio_file_path)}")

    for index, key in enumerate(API_KEYS):
        try:
            client = Groq(api_key=key)

            with open(audio_file_path, "rb") as file:
                # Multi-lang prompt to guide the AI
                multi_lang_prompt = "السلام عليكم، اليوم غادي نهضرو على coding و AI. Let's get started."

                transcription = client.audio.transcriptions.create(
                    file=(audio_file_path, file.read()),
                    model="whisper-large-v3",
                    prompt=multi_lang_prompt,
                    response_format="verbose_json",
                )

                # Prepare unified data structure
                output_data = {
                    "text": transcription.text,
                    "segments": transcription.segments
                }

                # Save to JSON
                with open(output_json, "w", encoding="utf-8") as f:
                    json.dump(output_data, f, ensure_ascii=False, indent=4)
                
                print(f" Success! Used Key #{index + 1}")
                return transcription.text

        except Exception as e:
            if "429" in str(e):
                print(f" Key #{index + 1} Rate Limited. Switching...")
                continue
            else:
                print(f" Error with Key #{index + 1}: {e}")
                continue

    print(" All 15 keys failed.")
    return None