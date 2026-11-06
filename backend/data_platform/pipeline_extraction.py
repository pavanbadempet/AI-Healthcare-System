"""
Pipeline Extraction Mixin.
Handles parallel extraction from databases (with incremental queries),
REST APIs, structured files, and real-time Kafka streams.
"""

import asyncio
import logging
import re
from typing import Any, Dict
from urllib.parse import urlparse

try:
    from pyspark.sql.functions import col
    from pyspark.sql.types import StructType
except Exception:
    col = None  # type: ignore
    StructType = None  # type: ignore

logger = logging.getLogger(__name__)
PIPELINE_FAILURE_MESSAGE = "Data pipeline failed. Please review operational logs."
SQL_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?$")


def _sql_literal(value: Any) -> str:
    """Format and escape values safely for SQL query literals."""
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    escaped = str(value).replace("'", "''")
    return f"'{escaped}'"


def _append_incremental_filter(query: str, incremental_column: str, last_extract_value: Any) -> str:
    """Safely append incremental filtering clause to extract query."""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Database extract query is required")
    if not SQL_IDENTIFIER_RE.fullmatch(incremental_column or ""):
        raise ValueError("Invalid incremental column")
    operator = "AND" if re.search(r"\bwhere\b", query, flags=re.IGNORECASE) else "WHERE"
    return f"{query} {operator} {incremental_column} > {_sql_literal(last_extract_value)}"


def _validate_api_base_url(base_url: str | None) -> str:
    """Validate API base URL scheme and netloc."""
    parsed = urlparse(base_url or "")
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("API base_url must use http or https")
    return str(base_url).rstrip("/")


class PipelineExtractionMixin:
    """Extraction methods for HealthcareDataPipeline."""

    async def _extract_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from multiple sources with parallel processing."""
        sources = config.get("sources", [])
        extract_results = {}

        extract_tasks = []
        for source in sources:
            task = self._extract_from_source(source)
            extract_tasks.append(task)

        results = await asyncio.gather(*extract_tasks, return_exceptions=True)

        for i, result in enumerate(results):
            source_name = sources[i].get("name", f"source_{i}")
            if isinstance(result, Exception):
                extract_results[source_name] = {"error": PIPELINE_FAILURE_MESSAGE}
            else:
                extract_results[source_name] = result

        return extract_results

    async def _extract_from_source(self, source_config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from specific source."""
        source_type = source_config.get("type")

        if source_type == "database":
            return await self._extract_from_database(source_config)
        elif source_type == "api":
            return await self._extract_from_api(source_config)
        elif source_type == "file":
            return await self._extract_from_file(source_config)
        elif source_type == "stream":
            return await self._extract_from_stream(source_config)
        else:
            raise ValueError(f"Unsupported source type: {source_type}")

    async def _extract_from_database(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from database with incremental loading."""
        connection_string = config.get("connection_string")
        query = config.get("query")
        incremental_column = config.get("incremental_column")
        last_extract_value = config.get("last_extract_value")

        if incremental_column and last_extract_value is not None:
            query = _append_incremental_filter(query, incremental_column, last_extract_value)

        df = (
            self.spark.read.format("jdbc")
            .options(
                url=connection_string,
                driver="org.postgresql.Driver",
                query=query,
            )
            .load()
        )

        max_value = None
        if incremental_column:
            max_row = df.agg({incremental_column: "max"}).collect()
            if max_row and max_row[0][0]:
                max_value = max_row[0][0]

        return {
            "dataframe": df,
            "record_count": df.count(),
            "max_incremental_value": max_value,
            "schema": df.schema,
        }

    async def _extract_from_api(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from REST API with pagination."""
        import requests

        base_url = config.get("base_url")
        endpoint = config.get("endpoint")
        headers = config.get("headers", {})
        pagination_param = config.get("pagination_param", "page")
        request_timeout = config.get("request_timeout_seconds", 30)
        base_url = _validate_api_base_url(base_url)

        all_data = []
        page = 1
        has_more = True

        while has_more:
            url = f"{base_url}/{endpoint}?{pagination_param}={page}"
            response = requests.get(url, headers=headers, timeout=request_timeout)

            if response.status_code != 200:
                break

            data = response.json()
            if isinstance(data, list):
                page_data = data
                has_more = len(page_data) > 0
            elif isinstance(data, dict):
                page_data = data.get("data", [])
                has_more = len(page_data) > 0
            else:
                break

            all_data.extend(page_data)
            page += 1

        if all_data:
            df = self.spark.createDataFrame(all_data)
        else:
            struct_type = StructType([]) if StructType else []
            df = self.spark.createDataFrame([], struct_type)

        return {
            "dataframe": df,
            "record_count": len(all_data),
            "pages_processed": page - 1,
        }

    async def _extract_from_file(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from files (CSV, JSON, Parquet)."""
        file_path = config.get("file_path")
        file_format = config.get("format", "csv")
        options = config.get("options", {})

        if file_format == "csv":
            df = self.spark.read.csv(file_path, header=True, **options)
        elif file_format == "json":
            df = self.spark.read.json(file_path, **options)
        elif file_format == "parquet":
            df = self.spark.read.parquet(file_path, **options)
        else:
            raise ValueError(f"Unsupported file format: {file_format}")

        return {
            "dataframe": df,
            "record_count": df.count(),
            "file_format": file_format,
        }

    async def _extract_from_stream(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from streaming sources (Kafka)."""
        stream_type = config.get("stream_type")

        if stream_type == "kafka":
            df = (
                self.spark.readStream.format("kafka")
                .option("kafka.bootstrap.servers", config.get("bootstrap_servers"))
                .option("subscribe", config.get("topic"))
                .load()
            )

            from pyspark.sql.functions import col as p_col
            from pyspark.sql.functions import from_json

            schema = config.get("schema")
            df = df.select(from_json(p_col("value").cast("string"), schema).alias("data"))
        else:
            raise ValueError(f"Unsupported stream type: {stream_type}")

        return {
            "streaming_dataframe": df,
            "stream_type": stream_type,
        }
