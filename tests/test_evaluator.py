from app.evaluator import evaluate


def test_good_answer_with_matching_evidence_passes():
    result = evaluate(
        question="What does the service do?",
        answer="The service evaluates model answers and reports reliability checks.",
        evidence=["The service evaluates model answers and reports reliability checks."],
    )
    assert result["passed"] is True
    assert result["score"] >= 0.7


def test_empty_answer_fails():
    result = evaluate(question="Question", answer="")
    assert result["passed"] is False
    assert next(c for c in result["checks"] if c["name"] == "non_empty")["passed"] is False


def test_schema_keys_are_checked():
    result = evaluate(
        question="Return JSON",
        answer='{"summary": "ok"}',
        expected_schema={"summary": "string", "confidence": "number"},
    )
    structure = next(c for c in result["checks"] if c["name"] == "structure")
    assert structure["passed"] is False


def test_batch_individual_scores_are_bounded():
    result = evaluate(question="Q", answer="A short response.")
    assert 0.0 <= result["score"] <= 1.0
