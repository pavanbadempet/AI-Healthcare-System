"""
Lakehouse SQL Engine — SQL Query Engine Over Clinical Data Lake.

Provides:
- SQL parsing and execution over in-memory lakehouse tables
- Parameterized query support
- Query profiling with execution metrics
- Result set pagination
- Warehouse endpoint abstraction for cloud lakehouse migration
"""

import time
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.data_platform.open_table_format import open_table_engine


class QueryProfile(BaseModel):
    """Execution profile for a SQL query."""
    query_id: str
    sql: str
    rows_scanned: int = 0
    rows_returned: int = 0
    execution_time_ms: float = 0.0
    warehouse_id: str = "default"


class SQLResultSet(BaseModel):
    """Result of a SQL query execution."""
    columns: List[str]
    rows: List[Dict[str, Any]]
    total_count: int
    profile: QueryProfile


class LakehouseSQLEngine:
    """
    Executes SQL-like queries against lakehouse ACID tables.

    Supports SELECT with WHERE, ORDER BY, LIMIT, and COUNT(*).
    Designed for open-standard lakehouse SQL migration compatibility.
    """

    def __init__(self, warehouse_id: str = "clinical-warehouse-01") -> None:
        self.warehouse_id = warehouse_id
        self._query_history: List[QueryProfile] = []

    def execute(self, sql: str, params: Optional[Dict[str, Any]] = None) -> SQLResultSet:
        """Execute a SQL query against registered lakehouse tables."""
        start = time.time()
        sql_upper = sql.strip().upper()

        # Parse table name from simple SELECT ... FROM <table>
        table_match = re.search(r"FROM\s+(\w+)", sql_upper)
        if not table_match:
            return self._empty_result(sql, start)

        table_name = table_match.group(1).lower()
        # Try to match against registered tables (case-insensitive)
        table = None
        for tname in open_table_engine.list_tables():
            if tname.lower() == table_name:
                table = open_table_engine.get_table(tname)
                break

        if table is None:
            return self._empty_result(sql, start)

        data = table.read()
        rows_scanned = len(data)

        # WHERE clause filtering
        where_match = re.search(r"WHERE\s+(\w+)\s*=\s*'?([^'\s]+)'?", sql, re.IGNORECASE)
        if where_match:
            col = where_match.group(1)
            val = where_match.group(2)
            data = [r for r in data if str(r.get(col, "")) == val]

        # COUNT(*) support
        if "COUNT(*)" in sql_upper:
            elapsed = (time.time() - start) * 1000
            profile = QueryProfile(
                query_id=f"Q-{int(time.time()*1000)}",
                sql=sql, rows_scanned=rows_scanned,
                rows_returned=1, execution_time_ms=round(elapsed, 3),
                warehouse_id=self.warehouse_id,
            )
            self._query_history.append(profile)
            return SQLResultSet(
                columns=["count"], rows=[{"count": len(data)}],
                total_count=1, profile=profile,
            )

        # ORDER BY
        order_match = re.search(r"ORDER\s+BY\s+(\w+)(?:\s+(ASC|DESC))?", sql, re.IGNORECASE)
        if order_match:
            col = order_match.group(1)
            desc = (order_match.group(2) or "ASC").upper() == "DESC"
            data.sort(key=lambda r: r.get(col, ""), reverse=desc)

        # LIMIT
        limit_match = re.search(r"LIMIT\s+(\d+)", sql, re.IGNORECASE)
        if limit_match:
            data = data[:int(limit_match.group(1))]

        columns = list(data[0].keys()) if data else []
        elapsed = (time.time() - start) * 1000

        profile = QueryProfile(
            query_id=f"Q-{int(time.time()*1000)}",
            sql=sql, rows_scanned=rows_scanned,
            rows_returned=len(data), execution_time_ms=round(elapsed, 3),
            warehouse_id=self.warehouse_id,
        )
        self._query_history.append(profile)

        return SQLResultSet(columns=columns, rows=data, total_count=len(data), profile=profile)

    def _empty_result(self, sql: str, start: float) -> SQLResultSet:
        """Return empty result set."""
        elapsed = (time.time() - start) * 1000
        profile = QueryProfile(
            query_id=f"Q-{int(time.time()*1000)}",
            sql=sql, rows_scanned=0, rows_returned=0,
            execution_time_ms=round(elapsed, 3),
            warehouse_id=self.warehouse_id,
        )
        return SQLResultSet(columns=[], rows=[], total_count=0, profile=profile)

    @property
    def query_history(self) -> List[QueryProfile]:
        """Return query execution history."""
        return list(self._query_history)


lakehouse_sql_engine = LakehouseSQLEngine()
