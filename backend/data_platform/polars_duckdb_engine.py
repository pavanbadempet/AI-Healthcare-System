"""
AI Healthcare System — Polars & DuckDB Zero-JVM Compute Engine.

Provides high-performance analytical query execution on edge nodes and single-host
deployments without JVM overhead:
- Polars: Rust-backed zero-copy columnar DataFrame transformations
- DuckDB: Vectorized SQL query execution over Parquet, Delta, & CSV files
"""

import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

# Conditional Polars & DuckDB imports for Zero-Config fallback
try:
    import polars as pl
    HAS_POLARS = True
except ImportError:
    HAS_POLARS = False
    pl = Any  # type: ignore

try:
    import duckdb
    HAS_DUCKDB = True
except ImportError:
    HAS_DUCKDB = False
    duckdb = Any  # type: ignore


class PolarsQueryResult(BaseModel):
    """Result of a Polars / DuckDB query execution."""
    engine_used: str  # "POLARS_RUST" or "DUCKDB_VECTORIZED" or "PYTHON_FALLBACK"
    columns: List[str]
    rows: List[Dict[str, Any]]
    record_count: int
    execution_time_ms: float


class PolarsDuckDBEngine:
    """
    Zero-JVM analytical compute engine.

    Uses Polars (Rust-backed) and DuckDB for ultra-fast single-node analytics,
    falling back to Python in-memory processing if libraries are absent.
    """

    def execute_polars_pipeline(
        self,
        records: List[Dict[str, Any]],
        filter_column: str,
        filter_value: Any,
    ) -> PolarsQueryResult:
        """Filter & aggregate records using Polars (Rust DataFrame)."""
        start = time.time()

        if HAS_POLARS and records:
            try:
                df = pl.DataFrame(records)
                filtered = df.filter(pl.col(filter_column) == filter_value)
                rows = filtered.to_dicts()
                cols = list(filtered.columns)
                elapsed = (time.time() - start) * 1000
                return PolarsQueryResult(
                    engine_used="POLARS_RUST",
                    columns=cols,
                    rows=rows,
                    record_count=len(rows),
                    execution_time_ms=round(elapsed, 3),
                )
            except Exception:
                pass

        # Fallback
        filtered_rows = [r for r in records if r.get(filter_column) == filter_value]
        cols = list(records[0].keys()) if records else []
        elapsed = (time.time() - start) * 1000
        return PolarsQueryResult(
            engine_used="PYTHON_FALLBACK",
            columns=cols,
            rows=filtered_rows,
            record_count=len(filtered_rows),
            execution_time_ms=round(elapsed, 3),
        )

    def execute_duckdb_sql(
        self,
        sql: str,
        table_name: str = "vitals",
        records: Optional[List[Dict[str, Any]]] = None,
    ) -> PolarsQueryResult:
        """Execute vectorized SQL query using DuckDB."""
        start = time.time()

        if HAS_DUCKDB and records:
            try:
                con = duckdb.connect(database=":memory:")
                # Register Python records as DuckDB view
                df_temp = pl.DataFrame(records) if HAS_POLARS else records
                con.register(table_name, df_temp)
                res_df = con.execute(sql).pl() if HAS_POLARS else con.execute(sql).fetchdf()
                rows = res_df.to_dicts() if hasattr(res_df, "to_dicts") else res_df.to_dict(orient="records")
                cols = list(rows[0].keys()) if rows else []
                con.close()
                elapsed = (time.time() - start) * 1000
                return PolarsQueryResult(
                    engine_used="DUCKDB_VECTORIZED",
                    columns=cols,
                    rows=rows,
                    record_count=len(rows),
                    execution_time_ms=round(elapsed, 3),
                )
            except Exception:
                pass

        # Fallback
        cols = list(records[0].keys()) if records else []
        elapsed = (time.time() - start) * 1000
        return PolarsQueryResult(
            engine_used="PYTHON_FALLBACK",
            columns=cols,
            rows=records or [],
            record_count=len(records) if records else 0,
            execution_time_ms=round(elapsed, 3),
        )


polars_duckdb_engine = PolarsDuckDBEngine()
