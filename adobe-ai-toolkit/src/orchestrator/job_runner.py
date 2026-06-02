from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.local.local_engine import LocalEngine
from src.api.cloud_service import CloudService
from src.utils.config import get_settings, Settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class JobRunner:
    """
    JobRunner orchestrates a single job lifecycle:
      - audio/video extraction
      - local transcription (via LocalEngine)
      - planning & generation (via CloudService)
      - artifact persistence

    The implementation uses mock cloud adapters (CloudService) and the
    LocalEngine mock transcription so you can exercise the pipeline before
    integrating real models.
    """

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self.local_engine = LocalEngine()
        self.cloud = CloudService(self.settings)

    def _make_output_dir(self, job_id: str) -> Path:
        out_base = Path(self.settings.storage_path) / "jobs" / job_id
        out_base.mkdir(parents=True, exist_ok=True)
        return out_base

    def _save_json(self, path: Path, data: Any) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def run_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a job described by `job` dict.

        Expected minimal job schema:
          {
            "job_id": "optional-string",
            "inputs": ["/path/to/clip1.mp4", "/path/to/clip2.mp4"],
            "persona": "optional-persona",
            "meta": { ... }
          }

        Returns a dictionary with job status and artifact paths.
        """
        job_id = job.get("job_id") or str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat() + "Z"
        outputs: Dict[str, Any] = {"job_id": job_id, "created_at": created_at, "status": "running"}

        out_dir = self._make_output_dir(job_id)
        outputs["output_dir"] = str(out_dir)

        inputs: List[str] = job.get("inputs") or job.get("clips") or []
        if not inputs:
            logger.error("No input clips provided for job %s", job_id)
            outputs["status"] = "failed"
            outputs["error"] = "no_inputs"
            return outputs

        transcripts: List[Dict[str, Any]] = []

        # Process each input sequentially (could be parallelized later)
        for idx, input_path in enumerate(inputs):
            try:
                logger.info("Job %s: processing input %s", job_id, input_path)
                audio_path = self.local_engine.extract_audio(input_path)
                transcript = self.local_engine.transcribe(audio_path)

                transcripts.append({
                    "input": input_path,
                    "audio_path": str(audio_path),
                    "transcript": transcript,
                })
            except Exception as e:
                logger.exception("Job %s: failed processing input %s: %s", job_id, input_path, e)
                transcripts.append({"input": input_path, "error": str(e)})

        # Persist transcripts
        transcripts_path = out_dir / "transcripts.json"
        self._save_json(transcripts_path, transcripts)
        outputs["transcripts_path"] = str(transcripts_path)

        # Build context bundle for planning
        context = {"job_id": job_id, "transcripts": transcripts, "meta": job.get("meta", {})}

        # Call CloudService.plan (mocked)
        try:
            persona = job.get("persona")
            plan = self.cloud.plan(context=context, persona=persona)
            outputs["plan"] = plan
            plan_path = out_dir / "plan.json"
            self._save_json(plan_path, plan)
            outputs["plan_path"] = str(plan_path)
            logger.info("Job %s: planning complete", job_id)
        except Exception as e:
            logger.exception("Job %s: planning failed: %s", job_id, e)
            outputs["status"] = "failed"
            outputs["error"] = f"planning_failed: {e}"
            return outputs

        # Use the plan to generate creative text (voiceover/script)
        try:
            prompt = plan.get("edit_plan") if isinstance(plan, dict) else str(plan)
            gen = self.cloud.generate(prompt=prompt)
            outputs["generation"] = gen
            gen_path = out_dir / "generation.json"
            self._save_json(gen_path, gen)
            outputs["generation_path"] = str(gen_path)
            logger.info("Job %s: generation complete", job_id)
        except Exception as e:
            logger.exception("Job %s: generation failed: %s", job_id, e)
            outputs["status"] = "failed"
            outputs["error"] = f"generation_failed: {e}"
            return outputs

        # Finalize
        outputs["status"] = "completed"
        outputs["completed_at"] = datetime.utcnow().isoformat() + "Z"

        # Persist job summary
        summary_path = out_dir / "job_summary.json"
        self._save_json(summary_path, outputs)
        outputs["summary_path"] = str(summary_path)

        logger.info("Job %s completed successfully. Artifacts: %s", job_id, out_dir)
        return outputs


if __name__ == "__main__":
    # Simple CLI runner for manual testing.
    import argparse

    parser = argparse.ArgumentParser(description="Run a single orchestration job (dry-run with mocks)")
    parser.add_argument("--job", help="Path to job JSON file. If omitted a sample job is used.", required=False)
    args = parser.parse_args()

    if args.job:
        jobfile = Path(args.job)
        if not jobfile.exists():
            print("Job file not found:", jobfile)
            raise SystemExit(1)
        job_data = json.loads(jobfile.read_text(encoding="utf-8"))
    else:
        # sample job
        job_data = {
            "inputs": ["examples/sample_clip.mp4"],
            "persona": "default_director",
        }

    runner = JobRunner()
    result = runner.run_job(job_data)
    print(json.dumps(result, indent=2))
