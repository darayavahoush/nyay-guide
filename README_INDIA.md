# India family-law module (no LLM, no voice)
- backend/app/india/engine.py   rule engine: remedies, venues, open conditions
- backend/app/india/intake.py   en/hi/ta keyword intake
- backend/app/india/agent.py    dialogue agent: information-gain question selection, plan + document checklist
- backend/app/india_api.py      POST /api/india/agent | /advise | /intake, GET /catalogue
- frontend/india.html           guided chat + form, EN/हि/த (http://localhost:5173/india.html)
- research/india_eval.py        engine vs baselines;  research/agent_eval.py  question efficiency
- tests/test_india.py           16 tests (run with the snippet in the chat, or pytest)
Gold labels are developer-written; Hindi/Tamil strings are not native-reviewed; remedy titles, plan steps and document lists are English only.
