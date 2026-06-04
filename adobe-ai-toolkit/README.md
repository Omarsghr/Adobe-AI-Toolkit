# Adobe AI Toolkit — Quick Onboarding

Welcome! This README gives a concise, friendly overview of the Adobe AI Toolkit to help teammates ("mates") get started quickly.

## What is this repository?

The Adobe AI Toolkit is a collection of tooling, scripts, and example panels for integrating AI-driven workflows with Adobe apps (CEP/UXP) and local services. It includes orchestration code, local engines, transcription and signal analysis, screenplay and creative director logic, and example UI assets.

Audience: developers, designers, and product teammates who need to run, extend, or integrate the toolkit.

## Quick highlights
- Local server and pipeline entry points: `main.py`, `server.py`, `main_pipeline.py`
- UI panel examples under: `Adobe-AI-Toolkit-Panel/`
- AI/agent logic lives in: `src/ai_logic/` and `src/screenplay/`
- Transcription, audio, and signal tools: `src/transcription/`, `src/signal_analysis/`

## Requirements
- Python 3.10+ recommended
- A virtual environment (optional but recommended)
- Recommended OS: any (development done on Windows in this workspace)

Install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If you prefer pipx/poetry, adapt accordingly (this project has a `pyproject.toml`).

## Quick start — run the main app
1. Activate your virtual environment as shown above.
2. Start the main script for development:

```powershell
python main.py
```

3. Or start the lightweight server (if you need API endpoints):

```powershell
python server.py
```

4. To run pipeline examples / tests:

```powershell
python main_pipeline.py
python integration_test_suite.py
```

Notes: these entry points are intentionally simple wrappers — check each file to see detailed CLI options and configs.

## Important files & directories
- `main.py` — primary local runner used for quick development flows
- `server.py` — exposes API endpoints for tool integration
- `main_pipeline.py` — orchestrates the end-to-end pipeline
- `integration_test_suite.py` — integration tests and smoke checks
- `src/` — main application source; key subfolders:
  - `ai_logic/` — director, visualist, keyword director modules
  - `screenplay/` — screenplay architecture, music/audio generator, subtitle generator
  - `transcription/` — whisper/local transcription, groq clients, audio processing
  - `signal_analysis/` — utilities for audio signal processing
  - `api/` — cloud provider abstractions and provider adapters
  - `data_formatter/` — payload validators and glue
  - `local/` — local engine implementations
  - `orchestrator/` — job runner, pipeline orchestration
  - `utils/` — configuration and small helpers
- `assets/` — example AI-generated images and audio placeholders
- `CEP/` & `Adobe-AI-Toolkit-Panel/` — panel manifests, host scripts, and UI samples for Adobe integration

## Common tasks for contributors
- Add a new provider: implement adapter under `src/api/providers/` and wire it into `src/api/cloud_service.py`.
- Update payload schemas: `src/data_formatter/payload_validator.py` — follow existing validators.
- Add an orchestration step: modify `src/orchestrator/job_runner.py` and associated pipeline docs under `src/screenplay/PIPELINE_DOCUMENTATION.md`.

## Debugging & troubleshooting
- Check logs printed to console — many modules use simple logging via `print` or Python `logging`.
- If dependencies fail to install, make sure your pip is up-to-date: `python -m pip install --upgrade pip`
- If tests fail, run individual modules with `python -m <module>` to get focused tracebacks.

## Contributing
- Fork/branch, follow the repo style, and make small PRs.
- Write unit or integration tests where appropriate; run `integration_test_suite.py` before opening a PR.
- Keep changes modular: add new features under `src/` and update README/docs.

## License & credits
This repo contains mixed assets and example code; consult `Adobe-AI-Toolkit-Panel/README.md` and other headers for third-party license details. If no license file exists in the repo root, ask the project owner for the intended license.

## Who to ask
If you're unsure where to begin, ask the original maintainers or search for `PROJECT_COMPLETION_SUMMARY.md` and `IMPLEMENTATION_GUIDE.md` in the repo root for onboarding notes.

— Quick, friendly guide to help mates get productive. Happy hacking!

