if (!(Test-Path ".venv")) { py -3.11 -m venv .venv }
. .\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
$env:PYTHONPATH = "backend"
uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000
