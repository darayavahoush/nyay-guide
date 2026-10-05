# Nyay Guide

**Which law, which court?** A rule-based dialogue agent that helps people in India work out which family-law remedies apply to them (divorce, maintenance, domestic-violence relief, dependants), where to file, and what to gather first. Available in English, Hindi and Tamil.

**Live:** https://nyay-guide.onrender.com (free tier, first load after idle takes about 30 seconds)

![Nyay Guide](docs/screenshot.png)

> **Decision support, not legal advice.** Every provision in the engine is written from the statutes and marked `verified: false`. It has not been reviewed by an advocate. Do not rely on it for a real case.

## What it does
You describe your situation in plain language. The agent reads it, asks only the questions whose answers would change the outcome, and builds a memorandum as you go.

- **Routes:** the applicable remedies, each with its provision, forum, venue options and authorities. Covers divorce, interim and permanent maintenance, maintenance of children and parents, the Domestic Violence Act and the Senior Citizens Act.
- **Personal laws:** Hindu (including Sikh, Jain, Buddhist), Muslim, Christian, Parsi and the Special Marriage Act.
- **Open conditions:** what still blocks a remedy, such as the one-year bar, the s.125(4) CrPC disqualifiers, or the separation period for mutual consent.
- **Sequence and documents:** a suggested order of filing with the documents to gather, plus the Rajnesh v. Neha disclosure checklist.
- **Live updates:** routes appear as soon as the law and your need are known, and update with each answer. Every question explains which routes it affects.
- **Languages:** the interface, questions and intake work in English, Hindi and Tamil. Remedy titles, plan steps and document lists are English only for now.
- **Print:** "Save as PDF" prints the memorandum on a white page.

## How it works
No LLM and no model downloads. Everything is deterministic and inspectable.

| Layer | File | Role |
|---|---|---|
| Intake | `backend/app/india/intake.py` | Keyword lexicon in en/hi/ta that guesses the law, claimant, needs and basic facts. Always confirmed with the user. |
| Rule engine | `backend/app/india/engine.py` | Takes the personal law and facts, returns remedies, venues, open conditions and disclosures. |
| Agent | `backend/app/india/agent.py` | Picks the next question by information gain (the unknown fact that best splits the engine's outcomes), stops when no fact can change the result, builds the plan and checklists. |
| API | `backend/app/india_api.py` | FastAPI routes. |
| Frontend | `frontend/` | React and Vite. |

The same service serves the built React app and the API, so there is one URL and no CORS setup in production.

## API
| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/india/agent` | One dialogue turn. Body: `session_id`, `text`, `answer`, `lang` (`en`, `hi`, `ta`). |
| `POST` | `/api/india/advise` | Stateless: send all facts, get remedies. |
| `POST` | `/api/india/intake` | Extract facts from free text. |
| `GET` | `/api/india/catalogue` | All remedies the engine knows. |
| `GET` | `/api/health` | Health check. |

Sessions are held in memory (last 500) and are lost on restart. Nothing is written to disk.

## Run locally
Requires Python 3.12 and Node 20.

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt pytest httpx

cd backend && uvicorn app.main:app --reload --port 8000     # terminal 1
cd frontend && npm install && npm run dev                   # terminal 2, http://localhost:5173
```

## Test and evaluate
```bash
PYTHONPATH=backend pytest tests -q                  # 19 tests
PYTHONPATH=backend python -m research.india_eval    # engine vs baselines
PYTHONPATH=backend python -m research.agent_eval    # question efficiency
```

On the 20 bundled scenarios the engine finds every required remedy with no wrong-law results, against 0.55 recall (religion-blind) and 0.58 (TF-IDF retrieval) for the baselines. The information-gain policy reaches 0.95 accuracy in 4.7 questions on average, against 15.3 for asking everything.

**Read these numbers with care.** The scenarios and their gold labels were written by the developer, not an advocate, so the engine scoring well is partly circular. They are a regression check, not evidence of legal accuracy.

## Deploy
`render.yaml` and the `Dockerfile` build the React app and serve it from FastAPI.

```bash
render services create --name nyay-guide --type web_service --runtime docker \
  --region singapore --plan free --repo https://github.com/<you>/nyay-guide --branch main
```
Set the health check path to `/api/health` in the Render dashboard. Pushes to `main` redeploy automatically.

## Known limits
- Provisions come from the developer's reading of the statutes. The Muslim, Christian and Parsi venue sections need the closest checking against indiacode.nic.in.
- Out of scope: foreign decrees, enforcement against a respondent abroad, limitation periods, and drafting of petitions.
- Hindi and Tamil strings are not native-reviewed.
- Intake is keyword-based and misses unusual phrasing, which is why the agent confirms the law, claimant and needs.
- Do not enter real names or case numbers. There is no authentication and no privacy review.

## Roadmap
- Advocate review of every provision and relabelling of the scenarios (100+ scenarios before any published numbers).
- Hindi and Tamil remedy titles, plan steps and documents.
- A learned intake classifier for Hindi and Tamil in place of the keyword lexicon.
- Printable one-page case brief for taking to an advocate.

## Layout
```
backend/app/india/   engine, intake, agent
backend/app/         FastAPI app and routes
frontend/src/        React app (App.jsx, strings.js, styles.css)
research/            scenarios and evaluation scripts
tests/               pytest suite
docs/                screenshot
```
