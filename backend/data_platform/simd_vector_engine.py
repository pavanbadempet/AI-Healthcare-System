"""
SIMD Vectorized Columnar Execution Engine for Healthcare Analytics.

Provides sub-millisecond, multi-predicate filtering and columnar aggregations
over dense contiguous memory buffers (PyArrow RecordBatches and NumPy arrays).

Designed for high-frequency ICU vitals surveillance, multi-condition registry scans,
and cohort identification without JVM or Spark overhead.
"""

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc


@dataclass
class ColumnarPredicate:
    column: str
    operator: str  # "==", "!=", ">", ">=", "<", "<=", "in", "between"
    value: Any  # Scalar or Tuple/List for "in" and "between"


@dataclass
class SimdExecutionMetrics:
    total_records_scanned: int
    matched_records: int
    selectivity_pct: float
    filter_latency_microseconds: float
    aggregate_latency_microseconds: float
    total_latency_microseconds: float
    throughput_records_per_sec: float


class SimdVectorExecutionEngine:
    """
    High-performance in-memory columnar execution engine leveraging PyArrow Compute C++ SIMD routines.
    """

    def __init__(self) -> None:
        pass

    def create_record_batch(self, records: List[Dict[str, Any]]) -> pa.Table:
        """
        Converts a list of dictionary clinical records into a zero-copy PyArrow Table.
        """
        if not records:
            return pa.table({})
        return pa.Table.from_pylist(records)

    def evaluate_predicates(
        self,
        table: pa.Table,
        predicates: List[ColumnarPredicate],
    ) -> Tuple[pa.Table, SimdExecutionMetrics]:
        """
        Executes vectorized boolean bitmask filtering using PyArrow SIMD compute kernels.
        """
        t0 = time.perf_counter()
        total_records = len(table)
        if total_records == 0 or not predicates:
            t_filt = (time.perf_counter() - t0) * 1_000_000
            metrics = SimdExecutionMetrics(
                total_records_scanned=total_records,
                matched_records=total_records,
                selectivity_pct=100.0 if total_records > 0 else 0.0,
                filter_latency_microseconds=round(t_filt, 2),
                aggregate_latency_microseconds=0.0,
                total_latency_microseconds=round(t_filt, 2),
                throughput_records_per_sec=0.0,
            )
            return table, metrics

        # Compose combined boolean mask
        combined_mask = None

        for pred in predicates:
            if pred.column not in table.column_names:
                continue
            col = table[pred.column]
            op = pred.operator.strip().lower()
            val = pred.value

            mask = None
            if op in ("==", "eq"):
                mask = pc.equal(col, val)
            elif op in ("!=", "neq"):
                mask = pc.not_equal(col, val)
            elif op in (">", "gt"):
                mask = pc.greater(col, val)
            elif op in (">=", "gte"):
                mask = pc.greater_equal(col, val)
            elif op in ("<", "lt"):
                mask = pc.less(col, val)
            elif op in ("<=", "lte"):
                mask = pc.less_equal(col, val)
            elif op == "in":
                mask = pc.is_in(col, pa.array(val))
            elif op == "between" and isinstance(val, (list, tuple)) and len(val) == 2:
                m_low = pc.greater_equal(col, val[0])
                m_high = pc.less_equal(col, val[1])
                mask = pc.and_(m_low, m_high)

            if mask is not None:
                if combined_mask is None:
                    combined_mask = mask
                else:
                    combined_mask = pc.and_(combined_mask, mask)

        t_filter_done = time.perf_counter()
        filter_latency_us = (t_filter_done - t0) * 1_000_000

        if combined_mask is not None:
            filtered_table = table.filter(combined_mask)
        else:
            filtered_table = table

        matched_count = len(filtered_table)
        total_time_us = (time.perf_counter() - t0) * 1_000_000
        sec = total_time_us / 1_000_000.0
        throughput = (total_records / sec) if sec > 0 else 0.0

        metrics = SimdExecutionMetrics(
            total_records_scanned=total_records,
            matched_records=matched_count,
            selectivity_pct=round((matched_count / max(total_records, 1)) * 100.0, 2),
            filter_latency_microseconds=round(filter_latency_us, 2),
            aggregate_latency_microseconds=0.0,
            total_latency_microseconds=round(total_time_us, 2),
            throughput_records_per_sec=round(throughput, 1),
        )

        return filtered_table, metrics

    def compute_columnar_aggregates(
        self,
        table: pa.Table,
        target_columns: List[str],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculates descriptive summary statistics (count, sum, mean, min, max, std, quartiles)
        over contiguous column arrays with SIMD acceleration.
        """
        aggregates: Dict[str, Dict[str, Any]] = {}
        if len(table) == 0:
            return aggregates

        for col_name in target_columns:
            if col_name not in table.column_names:
                continue
            col = table[col_name]
            # Convert to numpy for fast vectorized percentile calculation if numeric
            is_num = (
                pa.types.is_integer(col.type)
                or pa.types.is_floating(col.type)
                or pa.types.is_decimal(col.type)
            )
            if is_num:
                np_arr = col.to_numpy(zero_copy_only=False)
                # Filter out NaNs if any
                valid_arr = np_arr[~np.isnan(np_arr)] if np_arr.dtype.kind == "f" else np_arr
                if len(valid_arr) > 0:
                    aggregates[col_name] = {
                        "count": int(len(valid_arr)),
                        "sum": round(float(np.sum(valid_arr)), 4),
                        "mean": round(float(np.mean(valid_arr)), 4),
                        "std": round(float(np.std(valid_arr)), 4),
                        "min": round(float(np.min(valid_arr)), 4),
                        "max": round(float(np.max(valid_arr)), 4),
                        "p25": round(float(np.percentile(valid_arr, 25)), 4),
                        "median": round(float(np.median(valid_arr)), 4),
                        "p75": round(float(np.percentile(valid_arr, 75)), 4),
                        "p95": round(float(np.percentile(valid_arr, 95)), 4),
                    }
                else:
                    aggregates[col_name] = {"count": 0}
            else:
                # Categorical or string column
                counts = pc.value_counts(col)
                top_values = [
                    {"value": str(row["values"]), "count": int(row["counts"])}
                    for row in counts.to_pylist()[:5]
                ]
                aggregates[col_name] = {
                    "count": len(col),
                    "unique_cardinality": len(counts),
                    "top_frequencies": top_values,
                }

        return aggregates


simd_engine = SimdVectorExecutionEngine()
