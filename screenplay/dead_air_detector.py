import re
from typing import List, Tuple, Dict
import sqlite3
import os

class DeadAirDetector:
    """
    Detects dead air zones (silence, filler words, verbal tics).
    Uses both audio analysis and transcript parsing to identify zones for ripple deletion.
    """

    FILLER_WORDS = {
        'um', 'uh', 'uhh', 'umm', 'uhmm',
        'like', 'you know', 'i mean', 'basically',
        'so like', 'kind of', 'sort of', 'i guess',
        'literally', 'actually', 'honestly', 'right',
        'okay', 'so', 'anyway', 'err', 'ah', 'oh',
        'ahem', 'mhm', 'hmm', 'yeah', 'yup', 'nope'
    }

    def __init__(self, db_path: str = None):
        if db_path is None:
            # Calculate project root dynamically
            current_file = os.path.abspath(__file__)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
            db_path = os.path.join(project_root, "project_memory.db")
        self.db_path = db_path
        self.dead_air_zones = []

    def detect_from_silence_map(self, silence_intervals: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """
        Processes silence intervals from librosa analysis.
        Filters short pauses (< 0.3s are natural speech pauses).
        """
        dead_air = []

        for start, end in silence_intervals:
            duration = end - start
            # Threshold: silence > 0.5s is considered dead air
            if duration > 0.5:
                dead_air.append((start, end))

        self.dead_air_zones.extend(dead_air)
        return dead_air

    def detect_filler_words(
        self,
        transcript: str,
        word_timestamps: List[Dict]
    ) -> List[Tuple[float, float]]:
        """
        Detects filler words in the transcript using word-level timestamps.
        Returns list of (start_time, end_time) tuples for deletion.

        word_timestamps format:
        [
            {"word": "hello", "start": 0.0, "end": 0.5},
            {"word": "um", "start": 0.5, "end": 0.7},
            ...
        ]
        """
        filler_zones = []

        for word_data in word_timestamps:
            word = word_data.get("word", "").lower().strip()

            # Check if word is a filler
            if word in self.FILLER_WORDS or self._is_filler_pattern(word):
                start = word_data.get("start", 0)
                end = word_data.get("end", start + 0.1)
                filler_zones.append((start, end))

        self.dead_air_zones.extend(filler_zones)
        return filler_zones

    def _is_filler_pattern(self, word: str) -> bool:
        """Check for filler patterns not in the static list."""
        # Repeated vowels: "ahhhhh", "oooooh"
        if re.match(r'^[aeiou]{2,}h*$', word):
            return True
        # Stutters: "l-l-like"
        if re.match(r'^[a-z]-[a-z]', word):
            return True
        return False

    def detect_trailing_silence(
        self,
        word_timestamps: List[Dict],
        segment_end_time: float,
        trailing_threshold_seconds: float = 1.0
    ) -> List[Tuple[float, float]]:
        """
        Detects trailing silence after the last word in a segment.
        """
        trailing_zones = []

        if word_timestamps:
            last_word = word_timestamps[-1]
            last_word_end = last_word.get("end", segment_end_time)

            if segment_end_time - last_word_end > trailing_threshold_seconds:
                trailing_zones.append((last_word_end, segment_end_time))

        self.dead_air_zones.extend(trailing_zones)
        return trailing_zones

    def save_to_database(self) -> None:
        """Saves detected dead air zones to the SQLite database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("CREATE TABLE IF NOT EXISTS dead_air_zones (start REAL, end REAL, reason TEXT)")
            cursor.execute("DELETE FROM dead_air_zones")

            for start, end in self.dead_air_zones:
                cursor.execute(
                    "INSERT INTO dead_air_zones (start, end) VALUES (?, ?)",
                    (start, end)
                )

            conn.commit()
            conn.close()

            print(f" Saved {len(self.dead_air_zones)} dead air zones to database")

        except Exception as e:
            print(f" Error saving to database: {e}")

    def get_all_dead_air_zones(self) -> List[Tuple[float, float]]:
        """Returns all detected dead air zones, deduplicated and sorted."""
        # Sort and merge overlapping zones
        if not self.dead_air_zones:
            return []

        sorted_zones = sorted(set(self.dead_air_zones))
        merged = []

        for start, end in sorted_zones:
            if merged and start <= merged[-1][1]:
                # Merge overlapping zones
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))
            else:
                merged.append((start, end))

        return merged

    def create_deletion_report(self) -> Dict:
        """Creates a detailed report of all dead air zones."""
        zones = self.get_all_dead_air_zones()
        total_duration = sum(end - start for start, end in zones)

        return {
            "total_zones_detected": len(zones),
            "total_deletion_duration_seconds": round(total_duration, 2),
            "zones": [
                {
                    "start_timestamp": round(start, 3),
                    "end_timestamp": round(end, 3),
                    "duration_seconds": round(end - start, 3)
                }
                for start, end in zones
            ]
        }
