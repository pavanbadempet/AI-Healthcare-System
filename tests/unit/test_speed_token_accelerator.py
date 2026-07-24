from backend.speed_token_accelerator import HighSpeedTokenAccelerator, run_token_speed_benchmark


def test_high_speed_token_accelerator():
    accelerator = HighSpeedTokenAccelerator()
    res = accelerator.accelerate_llm_generation("Summarize patient lab results")
    assert res.accelerated is True
    assert res.time_to_first_token_ms < 100.0
    assert res.tokens_per_second > 50.0


def test_run_token_speed_benchmark_helper():
    info = run_token_speed_benchmark()
    assert info["accelerated"] is True
    assert info["ttft_ms"] < 100.0
