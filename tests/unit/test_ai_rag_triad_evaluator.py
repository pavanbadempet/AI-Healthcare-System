from backend.ai_rag_triad_evaluator import RAGTriadEvaluator, run_rag_triad_eval


def test_rag_triad_evaluator():
    evaluator = RAGTriadEvaluator()
    res = evaluator.evaluate_rag_completion(
        user_query="What medication is prescribed?",
        retrieved_contexts=["Patient prescribed Metformin 500mg daily."],
        generated_answer="The patient is taking Metformin 500mg daily [Source: Meds]."
    )
    assert res.grounding_passed is True
    assert res.hallucination_detected is False
    assert res.overall_triad_score >= 0.90


def test_run_rag_triad_eval_helper():
    info = run_rag_triad_eval()
    assert info["grounding_passed"] is True
    assert info["hallucination_detected"] is False
