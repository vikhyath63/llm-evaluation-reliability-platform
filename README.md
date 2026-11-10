# LLM Evaluation & Reliability Platform

A clean-room, locally runnable reference implementation for evaluating LLM outputs before they reach users. It includes deterministic structure, safety, factual-support, latency and cost checks; a FastAPI endpoint; a JSONL evaluation runner; and a small test suite.

## Quick start

Requirements: Python 3.11+

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs. The demo works without an API key: submit an answer and optional evidence, then inspect the scored checks. Run tests with `pytest`.

## Scope

This repository is an independent portfolio implementation, not Capgemini source code and not a claim of production certification. The default evaluators are deterministic and transparent. A model-based judge can be added behind the evaluator interface when credentials are configured.

## API

`POST /evaluate` accepts `question`, `answer`, optional `evidence`, `expected_schema`, and optional `latency_ms` / `estimated_cost_usd`. The response includes individual checks, an overall score, pass/fail, and actionable findings.

## Roadmap

- Add provider-backed judge adapters
- Persist runs and compare regressions
- Add CI quality gates and trace export
