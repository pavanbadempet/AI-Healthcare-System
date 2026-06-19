"""
DuckDB Vectorized Client for Lightweight Analytics & Telemetry
=============================================================
Provides high-performance vectorized query execution on Delta tables, Parquet, and CSV files,
decoupling analytical (OLAP) queries from transactional (OLTP) user databases.
"""

import logging
import os
from typing import Any, Dict, List, Optional

import duckdb

logger = logging.getLogger(__name__)

class DuckDBClient:
    """Singleton-style DuckDB client for running vectorized SQL queries on Lakehouse data."""
    _instance: Optional['DuckDBClient'] = None

    def __new__(cls, db_path: Optional[str] = None) -> 'DuckDBClient':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_db(db_path)
        return cls._instance

    def _init_db(self, db_path: Optional[str] = None):
        """Initialize the DuckDB database connection."""
        self.db_path = db_path or os.environ.get("DUCKDB_PATH", ":memory:")
        if self.db_path != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)

        try:
            self.conn = duckdb.connect(self.db_path)
            # Load required extensions (parquet support is built-in, but we can load others)
            self.conn.execute("INSTALL parquet; LOAD parquet;")
            logger.info("Initialized DuckDB connection to %s", self.db_path)
        except Exception as e:
            logger.error("Failed to initialize DuckDB: %s", e)
            # Fallback to in-memory
            self.conn = duckdb.connect(":memory:")

    def execute_query(self, query: str, params: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
        """Execute a query and return list of dictionaries."""
        try:
            res = self.conn.execute(query, params or [])
            cols = [desc[0] for desc in res.description]
            return [dict(zip(cols, row)) for row in res.fetchall()]
        except Exception as e:
            logger.error("DuckDB query failed: %s\nQuery: %s", e, query)
            return []

    def execute_to_df(self, query: str, params: Optional[List[Any]] = None) -> Any:
        """Execute query and return Pandas DataFrame."""
        try:
            return self.conn.execute(query, params or []).fetchdf()
        except Exception as e:
            logger.error("DuckDB query to DF failed: %s", e)
            import pandas as pd
            return pd.DataFrame()

    def execute_to_polars(self, query: str, params: Optional[List[Any]] = None) -> Any:
        """Execute query and return Polars DataFrame."""
        try:
            import polars as pl
            df_arrow = self.conn.execute(query, params or []).fetch_arrow_table()
            return pl.from_arrow(df_arrow)
        except Exception as e:
            logger.error("DuckDB query to Polars failed: %s", e)
            import polars as pl
            return pl.DataFrame()

    def query_delta_table(self, delta_table_path: str, query_suffix: str = "") -> List[Dict[str, Any]]:
        """Query a Delta table by reading its Parquet files directly using DuckDB."""
        # DuckDB can scan parquet files under the Delta log directory dynamically
        # For simplicity, we search the partition/data parquet files
        if not os.path.exists(delta_table_path):
            logger.warning("Delta table path %s does not exist", delta_table_path)
            return []

        parquet_glob = os.path.join(delta_table_path, "**", "*.parquet")
        query = f"SELECT * FROM read_parquet('{parquet_glob}') {query_suffix}"
        return self.execute_query(query)

    def close(self):
        """Close connection."""
        try:
            self.conn.close()
        except Exception:
            pass

# Singleton helper instance
def get_duckdb_client(db_path: Optional[str] = None) -> DuckDBClient:
    return DuckDBClient(db_path)
