import os
import json
from groq import Groq
from dotenv import load_dotenv

# Load the keys from your .env file
load_dotenv()

# Match the naming in your .env: GROQ_API_KEY_1 to GROQ_API_KEY_15
API_KEYS = [os.getenv(f"GROQ_API_KEY_{i}") for i in range(1, 16) if os.getenv(f"GROQ_API_KEY_{i}")]

def transcribe_with_groq(audio_file_path, output_json="map.json"):
    """
    High-speed cloud transcription using a bank of 15 keys.
    Extracts word-level timestamps from Whisper's verbose_json output.
    """
    if not API_KEYS:
        print(" Error: No API keys found in .env (Checked for GROQ_API_KEY_1 to 15)")
        return None

    if not os.path.exists(audio_file_path):
        print(f" Error: Audio file not found at {audio_file_path}")
        return None

    print(f" Sending to Groq Cloud: {os.path.basename(audio_file_path)}")

    for index, key in enumerate(API_KEYS):
        try:
            client = Groq(api_key=key)

            with open(audio_file_path, "rb") as file:
                # Multi-lang prompt to guide the AI for Moroccan/Arabic context
                multi_lang_prompt = (
                    "السلام عليكم، اليوم غادي نهضرو على coding و AI. "
                    "إزاي تعمل edit للفيديو بتاعك professionally وبطريقة سهلة. "
                )

                transcription = client.audio.transcriptions.create(
                    file=(audio_file_path, file.read()),
                    model="whisper-large-v3",
                    prompt=multi_lang_prompt,
                    response_format="verbose_json",
                    timestamp_granularities=["word"],
                )

                # Extract word-level timestamps from segments
                word_timestamps = _extract_word_timestamps(transcription)

                # Prepare the data dictionary with word-level precision
                output_data = {
                    "text": transcription.text,
                    "segments": transcription.segments,
                    "word_timestamps": word_timestamps,
                    "metadata": {
                        "language": getattr(transcription, 'language', 'unknown'),
                        "duration": sum(s.get('end', 0) - s.get('start', 0) for s in transcription.segments)
                    }
                }

                # Save results to JSON file
                with open(output_json, "w", encoding="utf-8") as f:
                    json.dump(output_data, f, ensure_ascii=False, indent=4)

                print(f" Success! Transcription saved using Key #{index + 1}")
                print(f"    Extracted {len(word_timestamps)} word-level timestamps")

                # Return both text and word timestamps for the Manager
                return {
                    "text": transcription.text,
                    "word_timestamps": word_timestamps,
                    "segments": transcription.segments
                }

        except Exception as e:
            error_str = str(e)
            if "429" in error_str:
                print(f" Key #{index + 1} Rate Limited. Switching to next...")
                continue
            else:
                print(f" Error with Key #{index + 1}: {type(e).__name__}: {error_str}")
                continue

    print(" All 15 keys failed or were rate limited.")
    return None


def _extract_word_timestamps(transcription):
    """
    Extracts word-level timestamps from Whisper verbose_json output.
    Whisper segments have words array with start/end times for each word.
    """
    word_timestamps = []

    # Safety check: transcription must exist and have segments
    if not hasattr(transcription, 'segments') or transcription.segments is None:
        return word_timestamps

    try:
        for segment in transcription.segments:
            if segment is None:
                continue

            if hasattr(segment, 'words') and segment.words:
                for word_data in segment.words:
                    try:
                        word_timestamps.append({
                            "word": getattr(word_data, 'word', ''),
                            "start": getattr(word_data, 'start', 0.0),
                            "end": getattr(word_data, 'end', 0.0),
                            "confidence": getattr(word_data, 'confidence', 1.0)
                        })
                    except (AttributeError, TypeError):
                        continue
    except TypeError:
        # Handle case where segments is not iterable
        return word_timestamps

    return word_timestamps