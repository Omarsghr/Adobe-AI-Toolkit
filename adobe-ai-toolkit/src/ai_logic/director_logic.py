import os
import json
from dotenv import load_dotenv
from openai import OpenAI

# تحميل الـ .env الموحد
load_dotenv(dotenv_path="c:/Users/dell/OneDrive/Desktop/.vscode/.env")


class NvidiaDirectorPipeline:
    def __init__(self):
        # جلب الـ 8 د الـ Keys
        self.keys = [os.getenv(f"NVIDIA_KEY_{i}") for i in range(
            1, 9) if os.getenv(f"NVIDIA_KEY_{i}")]
        self.current_index = 0

        if not self.keys:
            # Fallback إيلا مالقاش الـ 8 كيمشي للـ الكي العادي
            fallback = os.getenv("NVIDIA_API_KEY")
            if fallback:
                self.keys.append(fallback)
            else:
                raise ValueError(
                    "❌ [CRITICAL] No NVIDIA API keys found in .env file!")

        print(
            f"🎬 [Director Core] Active Pipeline loaded with {len(self.keys)} reasoning keys.")

    def get_client(self):
        """إنشاء الـ Client بالـ Key الحالي ف الـ تدوير"""
        return OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=self.keys[self.current_index]
        )

    def rotate_key(self):
        self.current_index = (self.current_index + 1) % len(self.keys)
        print(
            f"🔄 [Director Warning] Rate limit or error! Rotating to Key {self.current_index + 1}...")

    def generate_screenplay_blueprint(self, user_prompt: str) -> dict:
        """توليد الـ Screenplay مع الـ Thinking الحقيقي د الـ Nemotron-Omni"""

        system_instruction = (
            "You are an expert AI Video Director. Output ONLY a valid JSON object matching this structure: "
            "{'timeline_data': {'video_track_2_b_roll_images': [{'start_timestamp': 0, 'generation_prompt': 'detailed visual prompt'}]}}"
        )

        for _ in range(len(self.keys)):
            try:
                client = self.get_client()

                # 🚀 الـ Request الحقيقي اللي جربتيه دابا ورجع كيرعد
                completion = client.chat.completions.create(
                    model="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.4,
                    top_p=0.95,
                    max_tokens=4096,
                    extra_body={
                        "chat_template_kwargs": {"enable_thinking": True},
                        "reasoning_budget": 1024
                    }
                )

                raw_content = completion.choices[0].message.content

                # تنظيف الـ Response من أي Markdown د JSON
                if "```json" in raw_content:
                    raw_content = raw_content.split(
                        "```json")[1].split("```")[0]

                return json.loads(raw_content.strip())

            except json.JSONDecodeError:
                print(
                    "❌ [Parser Error] Nemotron output wasn't clean JSON. Retrying...")
                continue
            except Exception as e:
                print(f"⚠️ [API Connection Error] {e}")
                self.rotate_key()
                continue

        return {"error": "All keys exhausted or failed to output clean blueprint."}


# تشغيل الـ Pipeline
if __name__ == "__main__":
    director = NvidiaDirectorPipeline()
    test_prompt = "Create a cinematic sci-fi intro scene about Casablanca in 2026."
    print("🚀 Testing Nemotron Director Blueprint generation...")
    blueprint = director.generate_screenplay_blueprint(test_prompt)
    print(json.dumps(blueprint, indent=2))
