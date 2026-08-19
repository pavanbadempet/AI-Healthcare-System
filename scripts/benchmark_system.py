"""
AI Healthcare System — Production System Benchmark Harness.

Measures and reports end-to-end performance metrics for the SoftwareX
system architecture paper. Outputs structured JSON + markdown summary.

Metrics captured:
  1. ML model cold-start loading time (all 6 organ models)
  2. Per-model inference latency (p50 / p95 / p99) over N iterations
  3. Digital twin simulation latency
  4. Medallion pipeline (Bronze → Silver → Gold) throughput
  5. Process memory footprint (RSS) with all models loaded
  6. Concurrent prediction throughput (requests/sec)

Usage:
    python scripts/benchmark_system.py
    python scripts/benchmark_system.py --iterations 500 --output research/results/benchmark.json
"""

import argparse
import json
import os
import statistics
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _percentile(data: List[float], p: int) -> float:
    """Return the p-th percentile of a list of floats."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * (p / 100.0)
    f = int(k)
    c = f + 1
    if c >= len(sorted_data):
        return sorted_data[f]
    return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])


def _get_process_memory_mb() -> float:
    """Return current process RSS in MB (cross-platform)."""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)
    except ImportError:
        # Fallback for systems without psutil
        try:
            import resource
            return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
        except ImportError:
            return 0.0


# ---------------------------------------------------------------------------
# Benchmark: Model Cold-Start
# ---------------------------------------------------------------------------

def benchmark_model_cold_start() -> Dict[str, Any]:
    """Measure time to load all 6 organ ML models from disk."""
    print("\n[1/6] Benchmarking ML model cold-start loading...")

    from backend.model_service import ModelService

    start = time.perf_counter()
    svc = ModelService()
    svc.initialize()
    elapsed_ms = (time.perf_counter() - start) * 1000

    loaded = []
    for name, entry in svc._entries.items():
        loaded.append({
            "model": name,
            "status": entry.status.value,
            "version": entry.model_version,
        })

    mem_after = _get_process_memory_mb()

    result = {
        "cold_start_ms": round(elapsed_ms, 2),
        "models_loaded": len([m for m in loaded if m["status"] == "ready"]),
        "models_total": len(loaded),
        "memory_after_load_mb": round(mem_after, 1),
        "details": loaded,
    }
    print(f"   Cold start: {elapsed_ms:.1f} ms | {result['models_loaded']}/{result['models_total']} models | {mem_after:.0f} MB RSS")
    return result


# ---------------------------------------------------------------------------
# Benchmark: Per-Model Inference Latency
# ---------------------------------------------------------------------------

def benchmark_inference_latency(iterations: int = 200) -> Dict[str, Any]:
    """Measure per-model prediction latency over N iterations."""
    print(f"\n[2/6] Benchmarking inference latency ({iterations} iterations per model)...")

    from backend.model_service import model_service
    from backend.schemas.prediction import (
        DiabetesInput,
        HeartInput,
        KidneyInput,
        LiverInput,
        LungInput,
        StrokeInput,
    )

    dispatchers = {
        "heart": (
            model_service.predict_heart,
            HeartInput(age=63, sex=1, cp=3, trestbps=145, chol=233, fbs=1, restecg=0, thalach=150, exang=0, oldpeak=2.3, slope=0, ca=0, thal=1)
        ),
        "diabetes": (
            model_service.predict_diabetes,
            DiabetesInput(hypertension=1, high_chol=1, bmi=30.0, smoking_history=0, heart_disease=0, physical_activity=1, general_health=5, gender=1, age=55)
        ),
        "kidney": (
            model_service.predict_kidney,
            KidneyInput(age=48, bp=80, sg=1.021, al=1, su=1, rbc=0, pc=1, pcc=1, ba=0, bgr=140, bu=40, sc=1.2, sod=135, pot=4.5, hemo=12.5, pcv=38, wc=7500, rc=4.5, htn=1, dm=0, cad=0, appet=1, pe=0, ane=0)
        ),
        "liver": (
            model_service.predict_liver,
            LiverInput(age=65, gender=1, total_bilirubin=0.7, direct_bilirubin=0.1, alkaline_phosphotase=187, alamine_aminotransferase=16, aspartate_aminotransferase=18, total_proteins=6.8, albumin=3.3, albumin_and_globulin_ratio=0.9)
        ),
        "lungs": (
            model_service.predict_lungs,
            LungInput(gender=1, age=60, smoking=1, yellow_fingers=0, anxiety=0, peer_pressure=0, chronic_disease=0, fatigue=1, allergy=0, wheezing=1, alcohol=0, coughing=1, shortness_of_breath=1, swallowing_difficulty=0, chest_pain=1)
        ),
        "stroke": (
            model_service.predict_stroke,
            StrokeInput(gender=1, age=67, hypertension=0, heart_disease=1, smoking=0, bmi=36.6, glucose=228.69)
        ),
    }

    results = {}

    for model_name, (fn, input_data) in dispatchers.items():
        latencies_us = []
        for _ in range(iterations):
            start = time.perf_counter()
            try:
                fn(input_data)
            except Exception:
                pass
            elapsed_us = (time.perf_counter() - start) * 1_000_000
            latencies_us.append(elapsed_us)

        results[model_name] = {
            "iterations": iterations,
            "p50_us": round(_percentile(latencies_us, 50), 1),
            "p95_us": round(_percentile(latencies_us, 95), 1),
            "p99_us": round(_percentile(latencies_us, 99), 1),
            "mean_us": round(statistics.mean(latencies_us), 1),
            "std_us": round(statistics.stdev(latencies_us), 1) if len(latencies_us) > 1 else 0.0,
            "min_us": round(min(latencies_us), 1),
            "max_us": round(max(latencies_us), 1),
        }
        p50 = results[model_name]["p50_us"]
        p99 = results[model_name]["p99_us"]
        print(f"   {model_name:>10}: p50={p50:.0f} µs | p99={p99:.0f} µs")

    return results


# ---------------------------------------------------------------------------
# Benchmark: Digital Twin Simulation
# ---------------------------------------------------------------------------

def benchmark_digital_twin(iterations: int = 100) -> Dict[str, Any]:
    """Measure 10-year digital twin trajectory simulation latency."""
    print(f"\n[3/6] Benchmarking digital twin simulation ({iterations} iterations)...")

    from backend.clinical_digital_twin import digital_twin_engine
    from backend.schemas.peak_healthcare import DigitalTwinSimulationRequest

    req = DigitalTwinSimulationRequest(
        patient_id="BENCH-001",
        age=58,
        gender="Male",
        bmi=29.5,
        systolic_bp=148.0,
        fasting_glucose=126.0,
        egfr=62.0,
        ldl_cholesterol=155.0,
        hba1c=7.2,
        smoking_status="current",
        active_diagnoses=["Type 2 Diabetes", "Hypertension", "CKD Stage 3a"],
        proposed_interventions=["SGLT2i (Empagliflozin 10mg)", "Atorvastatin 40mg", "Lifestyle Mediterranean Diet"],
    )

    latencies_us = []
    for _ in range(iterations):
        start = time.perf_counter()
        digital_twin_engine.simulate_10_year_trajectory(req)
        elapsed_us = (time.perf_counter() - start) * 1_000_000
        latencies_us.append(elapsed_us)

    result = {
        "iterations": iterations,
        "p50_us": round(_percentile(latencies_us, 50), 1),
        "p95_us": round(_percentile(latencies_us, 95), 1),
        "p99_us": round(_percentile(latencies_us, 99), 1),
        "mean_us": round(statistics.mean(latencies_us), 1),
    }
    print(f"   Digital Twin 10-Year Sim: p50={result['p50_us']:.0f} µs | p99={result['p99_us']:.0f} µs")
    return result


# ---------------------------------------------------------------------------
# Benchmark: Medallion Pipeline Throughput
# ---------------------------------------------------------------------------

def benchmark_medallion_pipeline() -> Dict[str, Any]:
    """Measure Bronze → Silver → Gold medallion ETL throughput."""
    print("\n[4/6] Benchmarking Medallion Lakehouse pipeline throughput...")

    from backend.medallion_lakehouse_engine import MedallionLakehouseEngine

    engine = MedallionLakehouseEngine()

    batch_sizes = [100, 500, 1000]
    results = {}

    for n in batch_sizes:
        records = []
        for i in range(n):
            records.append({
                "patient_id": f"BENCH-{i:05d}",
                "name": f"Patient {i}",
                "email": f"p{i}@test.org",
                "gender": "Male" if i % 2 == 0 else "Female",
                "birth_date": "1970-01-15",
                "heart_rate": 72 + (i % 30),
                "systolic_bp": 120 + (i % 40),
                "spo2": 95 + (i % 5),
            })

        start = time.perf_counter()
        try:
            engine.run_full_pipeline(records)
        except Exception:
            pass
        elapsed_ms = (time.perf_counter() - start) * 1000
        throughput = n / (elapsed_ms / 1000) if elapsed_ms > 0 else 0

        results[f"batch_{n}"] = {
            "records": n,
            "elapsed_ms": round(elapsed_ms, 1),
            "throughput_records_per_sec": round(throughput, 0),
        }
        print(f"   Batch {n:>5}: {elapsed_ms:.1f} ms | {throughput:.0f} records/sec")

    return results


# ---------------------------------------------------------------------------
# Benchmark: Concurrent Throughput
# ---------------------------------------------------------------------------

def benchmark_concurrent_throughput(num_workers: int = 8, requests_per_worker: int = 50) -> Dict[str, Any]:
    """Measure concurrent prediction throughput using thread pool."""
    print(f"\n[5/6] Benchmarking concurrent throughput ({num_workers} workers × {requests_per_worker} requests)...")

    from concurrent.futures import ThreadPoolExecutor, as_completed
    from backend.model_service import model_service
    from backend.schemas.prediction import HeartInput

    if not model_service.is_available("heart"):
        model_service.initialize()

    heart_input = HeartInput(age=63, sex=1, cp=3, trestbps=145, chol=233, fbs=1, restecg=0, thalach=150, exang=0, oldpeak=2.3, slope=0, ca=0, thal=1)
    total_requests = num_workers * requests_per_worker

    def worker_fn() -> int:
        successes = 0
        for _ in range(requests_per_worker):
            try:
                res = model_service.predict_heart(heart_input)
                if res and res.prediction:
                    successes += 1
            except Exception as e:
                pass
        return successes

    start = time.perf_counter()
    total_success = 0
    with ThreadPoolExecutor(max_workers=num_workers) as pool:
        futures = [pool.submit(worker_fn) for _ in range(num_workers)]
        for f in as_completed(futures):
            total_success += f.result()
    elapsed_sec = time.perf_counter() - start

    rps = total_success / elapsed_sec if elapsed_sec > 0 else 0

    result = {
        "workers": num_workers,
        "total_requests": total_requests,
        "successful": total_success,
        "elapsed_sec": round(elapsed_sec, 3),
        "requests_per_sec": round(rps, 1),
    }
    print(f"   Concurrent: {total_success}/{total_requests} successful | {rps:.0f} req/sec")
    return result


# ---------------------------------------------------------------------------
# Benchmark: Memory Footprint
# ---------------------------------------------------------------------------

def benchmark_memory_footprint() -> Dict[str, Any]:
    """Report current process memory footprint."""
    print("\n[6/6] Measuring memory footprint...")

    rss_mb = _get_process_memory_mb()

    # Measure model file sizes on disk
    backend_dir = os.path.join(os.path.dirname(__file__), "..", "backend")
    model_files = {}
    for fname in os.listdir(backend_dir):
        if fname.endswith((".pkl", ".onnx")):
            fpath = os.path.join(backend_dir, fname)
            size_mb = os.path.getsize(fpath) / (1024 * 1024)
            model_files[fname] = round(size_mb, 2)

    total_disk_mb = sum(model_files.values())

    result = {
        "process_rss_mb": round(rss_mb, 1),
        "model_disk_total_mb": round(total_disk_mb, 1),
        "model_files": model_files,
    }
    print(f"   Process RSS: {rss_mb:.0f} MB | Models on disk: {total_disk_mb:.1f} MB")
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    """Execute full benchmark suite and output results."""
    parser = argparse.ArgumentParser(description="AI Healthcare System Benchmark Harness")
    parser.add_argument("--iterations", type=int, default=200, help="Iterations per inference benchmark")
    parser.add_argument("--output", type=str, default=None, help="Output JSON file path")
    args = parser.parse_args()

    print("=" * 72)
    print("  AI HEALTHCARE SYSTEM — PRODUCTION BENCHMARK HARNESS")
    print(f"  Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 72)

    overall_start = time.perf_counter()

    report: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version.split()[0],
        "platform": sys.platform,
    }

    # Run benchmarks
    report["cold_start"] = benchmark_model_cold_start()
    report["inference_latency"] = benchmark_inference_latency(iterations=args.iterations)
    report["digital_twin"] = benchmark_digital_twin(iterations=args.iterations)

    try:
        report["medallion_pipeline"] = benchmark_medallion_pipeline()
    except Exception as e:
        report["medallion_pipeline"] = {"error": str(e)}
        print(f"   Medallion benchmark skipped: {e}")

    report["concurrent_throughput"] = benchmark_concurrent_throughput()
    report["memory"] = benchmark_memory_footprint()

    total_sec = time.perf_counter() - overall_start
    report["total_benchmark_duration_sec"] = round(total_sec, 2)

    # Output
    output_path = args.output
    if not output_path:
        os.makedirs(os.path.join(os.path.dirname(__file__), "..", "research", "results"), exist_ok=True)
        output_path = os.path.join(os.path.dirname(__file__), "..", "research", "results", "benchmark_report.json")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    # Print summary table
    print("\n" + "=" * 72)
    print("  BENCHMARK SUMMARY")
    print("=" * 72)
    print(f"  {'Metric':<45} {'Value':>20}")
    print("  " + "-" * 66)
    print(f"  {'Cold Start (all models)':<45} {report['cold_start']['cold_start_ms']:>17.1f} ms")
    print(f"  {'Models Loaded':<45} {report['cold_start']['models_loaded']:>17d}/{report['cold_start']['models_total']}")

    for model, data in report["inference_latency"].items():
        if isinstance(data, dict) and "p50_us" in data:
            print(f"  {f'Inference {model} (p50/p99)':<45} {data['p50_us']:>7.0f} / {data['p99_us']:>7.0f} µs")

    dt = report.get("digital_twin", {})
    if "p50_us" in dt:
        print(f"  {'Digital Twin 10-Yr Sim (p50/p99)':<45} {dt['p50_us']:>7.0f} / {dt['p99_us']:>7.0f} µs")

    ct = report.get("concurrent_throughput", {})
    if "requests_per_sec" in ct:
        print(f"  {'Concurrent Throughput':<45} {ct['requests_per_sec']:>15.0f} req/s")

    mem = report.get("memory", {})
    if "process_rss_mb" in mem:
        print(f"  {'Process Memory (RSS)':<45} {mem['process_rss_mb']:>17.0f} MB")
        print(f"  {'Model Artifacts on Disk':<45} {mem['model_disk_total_mb']:>15.1f} MB")

    print(f"\n  Total benchmark duration: {total_sec:.1f}s")
    print(f"  Results saved to: {output_path}")
    print("=" * 72)


if __name__ == "__main__":
    main()
