from typing import List, Dict, Tuple, Optional
import re

class SubtitleGenerator:
    """
    Maps word-level timestamps to subtitle blocks.
    Intelligently groups words for on-screen display with cinematic timing.
    """

    def __init__(self, words_per_subtitle: int = 6, max_line_width: int = 42):
        self.words_per_subtitle = words_per_subtitle
        self.max_line_width = max_line_width
        self.subtitles = []

    def generate_from_word_timestamps(
        self,
        word_timestamps: List[Dict]
    ) -> List[Dict]:
        """
        Converts word-level timestamps into grouped subtitle blocks.

        Input format:
        [
            {"word": "Hello", "start": 0.0, "end": 0.5, "confidence": 0.99},
            {"word": "world", "start": 0.5, "end": 0.9},
            ...
        ]

        Output format:
        [
            {
                "start_time": 0.0,
                "end_time": 0.9,
                "subtitle_text": "Hello world",
                "word_count": 2,
                "extracted_keywords": ["hello", "world"]
            },
            ...
        ]
        """
        if not word_timestamps:
            return []

        subtitle_blocks = []
        word_buffer = []
        buffer_start_time = None

        for i, word_data in enumerate(word_timestamps):
            word = word_data.get("word", "").strip()
            start = word_data.get("start", 0)
            end = word_data.get("end", start + 0.1)

            # Skip empty words
            if not word:
                continue

            # Initialize buffer on first word
            if not word_buffer:
                buffer_start_time = start

            word_buffer.append((word, end))

            # Create subtitle block when:
            # 1. We've accumulated enough words
            # 2. We're at the end of the list
            # 3. A long pause detected (gap > 0.8s)
            should_create_block = (
                len(word_buffer) >= self.words_per_subtitle or
                i == len(word_timestamps) - 1 or
                (i < len(word_timestamps) - 1 and
                 word_timestamps[i + 1].get("start", 0) - end > 0.8)
            )

            if should_create_block and word_buffer:
                block = self._create_subtitle_block(
                    word_buffer, buffer_start_time
                )
                if block:
                    subtitle_blocks.append(block)
                word_buffer = []
                buffer_start_time = None

        self.subtitles = subtitle_blocks
        return subtitle_blocks

    def _create_subtitle_block(
        self,
        word_buffer: List[Tuple[str, float]],
        start_time: float
    ) -> Dict:
        """Creates a single subtitle block from a word buffer."""
        words = [w[0] for w in word_buffer]
        end_time = word_buffer[-1][1]

        # Join words and clean up
        subtitle_text = " ".join(words)

        # Split into lines if too long
        lines = self._wrap_text(subtitle_text)
        formatted_text = "\n".join(lines)

        # Extract keywords (words > 3 chars, excluding articles)
        keywords = self._extract_keywords(words)

        return {
            "start_time": round(start_time, 3),
            "end_time": round(end_time, 3),
            "subtitle_text": formatted_text,
            "raw_text": subtitle_text,
            "word_count": len(words),
            "duration_seconds": round(end_time - start_time, 3),
            "extracted_keywords": keywords
        }

    def _wrap_text(self, text: str, width: int = None) -> List[str]:
        """Wraps text to max line width for on-screen display."""
        width = width or self.max_line_width
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            if len(test_line) <= width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

        return lines

    def _extract_keywords(self, words: List[str], min_length: int = 4) -> List[str]:
        """Extracts meaningful keywords from word list."""
        articles = {'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 'to', 'for', 'in', 'on', 'at', 'of'}
        keywords = [
            w.lower() for w in words
            if len(w) >= min_length and w.lower() not in articles
        ]
        return list(dict.fromkeys(keywords))  # Remove duplicates while preserving order

    def generate_srt_format(self) -> str:
        """
        Generates subtitles in SRT format for Premiere Pro import.

        Format:
        1
        00:00:00,000 --> 00:00:05,000
        Subtitle text here

        2
        00:00:05,000 --> 00:00:10,000
        Next subtitle text
        """
        srt_content = []

        for idx, subtitle in enumerate(self.subtitles, 1):
            start_str = self._seconds_to_srt_time(subtitle["start_time"])
            end_str = self._seconds_to_srt_time(subtitle["end_time"])

            srt_content.append(f"{idx}\n{start_str} --> {end_str}\n{subtitle['subtitle_text']}\n")

        return "\n".join(srt_content)

    def generate_vtt_format(self) -> str:
        """Generates subtitles in VTT format (WebVTT)."""
        vtt_content = ["WEBVTT\n"]

        for subtitle in self.subtitles:
            start_str = self._seconds_to_srt_time(subtitle["start_time"])
            end_str = self._seconds_to_srt_time(subtitle["end_time"])

            vtt_content.append(f"{start_str} --> {end_str}")
            vtt_content.append(subtitle["subtitle_text"])
            vtt_content.append("")

        return "\n".join(vtt_content)

    @staticmethod
    def _seconds_to_srt_time(seconds: float) -> str:
        """Converts seconds to SRT time format: HH:MM:SS,mmm"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)

        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def save_srt(self, filepath: str) -> None:
        """Saves subtitles to SRT file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.generate_srt_format())
        print(f" SRT subtitles saved: {filepath}")

    def save_vtt(self, filepath: str) -> None:
        """Saves subtitles to VTT file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.generate_vtt_format())
        print(f" VTT subtitles saved: {filepath}")

    def get_subtitles(self) -> List[Dict]:
        """Returns all generated subtitle blocks."""
        return self.subtitles

    def create_subtitle_report(self) -> Dict:
        """Creates a detailed report of subtitle generation."""
        return {
            "total_subtitles": len(self.subtitles),
            "total_duration_seconds": round(
                self.subtitles[-1]["end_time"] - self.subtitles[0]["start_time"]
                if self.subtitles else 0, 2
            ),
            "average_words_per_subtitle": round(
                sum(s["word_count"] for s in self.subtitles) / len(self.subtitles)
                if self.subtitles else 0, 1
            ),
            "total_words": sum(s["word_count"] for s in self.subtitles),
            "unique_keywords": list(dict.fromkeys(
                [k for s in self.subtitles for k in s["extracted_keywords"]]
            ))
        }
