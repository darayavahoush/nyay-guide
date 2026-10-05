# Nyay Guide

Which law, which court? A rule-based dialogue agent for Indian family law (divorce, maintenance, domestic violence relief, dependants) in English, Hindi and Tamil. No LLM, no voice.
A rule engine decides; an information-gain policy chooses the next question. Decision support only, not legal advice. Provisions are unverified by an advocate.

## Run locally
```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt pytest httpx
cd backend && uvicorn app.main:app --reload --port 8000      # tab 1
cd frontend && npm install && npm run dev                     # tab 2 -> http://localhost:5173
```
Tests: `PYTHONPATH=backend pytest tests -q`. Evaluations: `PYTHONPATH=backend python -m research.india_eval` and `python -m research.agent_eval`.

## Deploy
`render.yaml` + `Dockerfile` build the React app and serve it from the FastAPI service on one URL.
