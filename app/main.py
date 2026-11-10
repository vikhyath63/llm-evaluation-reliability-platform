from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.evaluator import evaluate

app = FastAPI(
    title="LLM Evaluation & Reliability Platform",
    version="0.1.0",
    description="Local-first, explainable evaluation checks for LLM outputs.",
)


class EvaluationRequest(BaseModel):
    question: str = Field(min_length=1, max_length=10_000)
    answer: str = Field(max_length=100_000)
    evidence: list[str] | None = None
    expected_schema: dict[str, object] | None = None
    latency_ms: float | None = Field(default=None, ge=0)
    estimated_cost_usd: float | None = Field(default=None, ge=0)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "llm-evaluation-reliability-platform"}


@app.post("/evaluate")
def evaluate_output(request: EvaluationRequest) -> dict:
    return evaluate(**request.model_dump())


@app.post("/evaluate/batch")
def evaluate_batch(requests: list[EvaluationRequest]) -> dict:
    results = [evaluate(**item.model_dump()) for item in requests]
    return {
        "count": len(results),
        "passed": sum(1 for item in results if item["passed"]),
        "failed": sum(1 for item in results if not item["passed"]),
        "results": results,
    }
