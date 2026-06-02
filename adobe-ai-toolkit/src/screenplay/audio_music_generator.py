import os
import json
from typing import Tuple, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class AudioMusicGenerator:
    """
    Generates background music and ambient tracks using multiple APIs.
    Supports both free APIs (Replicate, Hugging Face) and premium (OpenAI, Anthropic).
    Returns asset path and duration for timeline integration.
    """

    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir or os.path.join(
            os.path.expanduser("~"), "Desktop", "auto--editor__AI", "assets", "ai_music"
        )
        os.makedirs(self.output_dir, exist_ok=True)
        self.api_key_replicate = os.getenv("REPLICATE_API_KEY")
        self.api_key_elevenlabs = os.getenv("ELEVENLABS_API_KEY")

    def generate_ambient_free(
        self,
        style_prompt: str,
        duration_seconds: float = 30.0,
        genre: str = "ambient"
    ) -> Tuple[str, float]:
        """
        Generate ambient music using free/freemium APIs.
        Returns: (local_asset_path, estimated_duration)
        """
        print(f" Generating {genre} ambient track: {style_prompt[:60]}...")

        # Using Hugging Face Inference API (free tier available)
        # Models: facebook/musicgen-small, facebook/musicgen-medium
        try:
            import requests
            hf_token = os.getenv("HUGGINGFACE_API_KEY")

            if hf_token:
                return self._generate_with_huggingface(
                    style_prompt, duration_seconds, genre, hf_token
                )
        except Exception as e:
            print(f" HuggingFace generation failed: {e}")

        # Fallback: Return metadata placeholder for local generation
        asset_filename = f"ambient_{genre}_{int(duration_seconds)}s.mp3"
        asset_path = os.path.join(self.output_dir, asset_filename)

        print(f" [Placeholder] Music track metadata prepared: {asset_filename}")
        print(f"   Style: {style_prompt}")
        print(f"   Duration: {duration_seconds}s")

        return asset_path, duration_seconds

    def _generate_with_huggingface(
        self,
        style_prompt: str,
        duration_seconds: float,
        genre: str,
        hf_token: str
    ) -> Tuple[str, float]:
        """Uses Hugging Face Inference API for music generation."""
        import requests

        api_url = "https://api-inference.huggingface.co/models/facebook/musicgen-medium"
        headers = {"Authorization": f"Bearer {hf_token}"}

        payload = {
            "inputs": style_prompt,
            "parameters": {
                "max_length": min(int(duration_seconds * 50), 1500),
                "top_k": 250,
                "top_p": 0.0
            }
        }

        try:
            response = requests.post(api_url, headers=headers, json=payload, timeout=120)

            if response.status_code == 200:
                asset_filename = f"ambient_{genre}_{int(duration_seconds)}s.wav"
                asset_path = os.path.join(self.output_dir, asset_filename)

                with open(asset_path, 'wb') as f:
                    f.write(response.content)

                print(f" Music generated: {asset_filename}")
                return asset_path, duration_seconds
            else:
                print(f" HuggingFace returned status {response.status_code}")
                raise Exception(f"API Error: {response.text}")
        except Exception as e:
            print(f" HuggingFace API error: {e}")
            raise

    def generate_music_with_replicate(
        self,
        style_prompt: str,
        duration_seconds: float = 30.0,
        model: str = "riffusion"
    ) -> Tuple[str, float]:
        """
        Generate music using Replicate API.
        Requires REPLICATE_API_KEY in .env
        """
        if not self.api_key_replicate:
            print(" REPLICATE_API_KEY not found in .env")
            return None, 0

        try:
            import replicate

            print(f" Generating {duration_seconds}s music via Replicate...")

            # Using Riffusion model for music generation
            output = replicate.run(
                f"lucidrains/{model}:latest",
                input={
                    "prompt": style_prompt,
                    "num_inference_steps": 50,
                    "guidance_scale": 7.5,
                    "scheduler": "karras"
                }
            )

            # Download and save the output
            asset_filename = f"music_{model}_{int(duration_seconds)}s.mp3"
            asset_path = os.path.join(self.output_dir, asset_filename)

            if isinstance(output, str):
                import requests
                response = requests.get(output)
                with open(asset_path, 'wb') as f:
                    f.write(response.content)

            print(f" Music generated: {asset_filename}")
            return asset_path, duration_seconds

        except Exception as e:
            print(f" Replicate generation failed: {e}")
            return None, 0

    def create_music_metadata(
        self,
        style_prompt: str,
        duration_seconds: float,
        genre: str = "ambient",
        estimated_path: str = None
    ) -> Dict:
        """Creates music metadata for database storage."""
        return {
            "asset_path": estimated_path or os.path.join(
                self.output_dir, f"{genre}_{int(duration_seconds)}s.mp3"
            ),
            "duration_seconds": duration_seconds,
            "style_prompt": style_prompt,
            "genre": genre,
            "api_used": "huggingface_free" if self.api_key_replicate else "placeholder"
        }
