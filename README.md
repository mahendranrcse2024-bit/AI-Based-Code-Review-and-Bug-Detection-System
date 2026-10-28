# AI-Based Code Review and Bug Detection

A college-project-ready, static-analysis-first code review application. It accepts pasted or uploaded source, stores reviews in SQLite, exposes a FastAPI API, and provides a Streamlit dashboard. Python analysis uses the Python AST and Ruff when installed; other supported extensions are accepted but clearly report that analysis is not implemented.

## Features

- Safe source validation: extension, size, empty, binary/NUL, and path traversal checks.
- Deterministic findings with line, rule, category, severity, evidence, tool, fix, and status.
- Optional OpenAI-compatible AI explanations; no API key is required for static analysis.
- SQLite history and JSON/CSV/HTML exports.
- No uploaded code is executed.

## Run locally

Linux/macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # optional; export variables from it as needed
uvicorn app.main:app --reload
# in a second terminal: streamlit run app/ui/dashboard.py
```

Windows PowerShell:
```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
# second terminal
streamlit run app/ui/dashboard.py
```

FastAPI docs are at http://127.0.0.1:8000/docs and the dashboard at http://localhost:8501.

## Optional AI

Set `AI_API_KEY`, optionally `AI_API_BASE`, and `AI_MODEL`. The API exposes an explicit AI endpoint for a finding. AI output is labeled advisory, code is treated as untrusted input, and service failures preserve deterministic findings. Do not send sensitive code to an external provider without consent.

## Tests

Run `pytest -q`. Tests use mocked/local behavior and do not require an AI key. The default workflow never executes uploaded code. For production, add authentication, per-user authorization, encrypted storage, retention controls, and an isolated worker for any future dynamic analysis.

## Limitations

Python is the only fully implemented analysis language. Ruff is optional and partial results are retained if it is unavailable. AST heuristics are suggestions, not proof of defects; findings require human verification. SQLite is suitable for local/student use, not high-concurrency deployment.
