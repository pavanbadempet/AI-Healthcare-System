"""
Agentic Business Intelligence Engine — AI/BI Natural Language Analytics.

Provides:
- Natural language to SQL translation
- Agentic dashboard metric computation
- Automated clinical KPI summarization
- Self-serve analytics for clinicians (no SQL required)
"""

import time
from typing import Any, Dict, List

from pydantic import BaseModel, Field

from backend.data_platform.lakehouse_sql import lakehouse_sql_engine


class BIQuery(BaseModel):
    """A natural-language BI query."""
    question: str
    generated_sql: str = ""
    answer: str = ""
    metrics: Dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: float = 0.0


class DashboardWidget(BaseModel):
    """A single widget on an agentic BI dashboard."""
    widget_id: str
    title: str
    metric_value: Any = None
    chart_type: str = "KPI"  # "KPI", "BAR", "LINE", "TABLE"
    data: List[Dict[str, Any]] = Field(default_factory=list)


class AgenticBIEngine:
    """
    Translates natural-language questions into SQL, executes against
    the lakehouse, and returns summarized business intelligence answers.
    """

    # Simple keyword → SQL mapping for common clinical BI queries
    _NL_PATTERNS: Dict[str, str] = {
        "how many patients": "SELECT COUNT(*) FROM {table}",
        "total patients": "SELECT COUNT(*) FROM {table}",
        "average": "SELECT * FROM {table}",
        "list all": "SELECT * FROM {table} LIMIT 100",
        "show me": "SELECT * FROM {table} LIMIT 50",
    }

    def ask(self, question: str, table: str = "patients") -> BIQuery:
        """Answer a natural-language BI question."""
        start = time.time()
        q_lower = question.lower()

        # Match to SQL pattern
        sql = f"SELECT * FROM {table} LIMIT 50"
        for pattern, template in self._NL_PATTERNS.items():
            if pattern in q_lower:
                sql = template.format(table=table)
                break

        # Execute against lakehouse
        result = lakehouse_sql_engine.execute(sql)
        elapsed = (time.time() - start) * 1000

        # Synthesize answer
        if "COUNT" in sql.upper():
            count = result.rows[0].get("count", 0) if result.rows else 0
            answer = f"There are {count} records in '{table}'."
            metrics = {"count": count}
        else:
            answer = f"Returned {result.total_count} records from '{table}'."
            metrics = {"rows_returned": result.total_count}

        return BIQuery(
            question=question,
            generated_sql=sql,
            answer=answer,
            metrics=metrics,
            execution_time_ms=round(elapsed, 3),
        )

    def build_dashboard(self, table: str, title: str = "Clinical Dashboard") -> List[DashboardWidget]:
        """Auto-generate a clinical KPI dashboard from a table."""
        widgets: List[DashboardWidget] = []

        # Total records KPI
        count_result = lakehouse_sql_engine.execute(f"SELECT COUNT(*) FROM {table}")
        count = count_result.rows[0].get("count", 0) if count_result.rows else 0
        widgets.append(DashboardWidget(
            widget_id="W-TOTAL", title=f"Total Records — {table}",
            metric_value=count, chart_type="KPI",
        ))

        # Sample data table
        sample = lakehouse_sql_engine.execute(f"SELECT * FROM {table} LIMIT 10")
        widgets.append(DashboardWidget(
            widget_id="W-SAMPLE", title=f"Recent Records — {table}",
            metric_value=sample.total_count, chart_type="TABLE",
            data=sample.rows,
        ))

        return widgets


agentic_bi_engine = AgenticBIEngine()
