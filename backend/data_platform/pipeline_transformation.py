"""
Pipeline Transformation Mixin.
Handles transformations: filtering, aggregations, joins, deduping,
null handling, terminology lookups (SNOMED, RxNorm, ICD-10), and merges.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

try:
    from pyspark.sql import DataFrame as SparkDF
    from pyspark.sql.functions import avg, col, count, sum
    from pyspark.sql.functions import max as spark_max
    from pyspark.sql.functions import min as spark_min
except Exception:
    SparkDF = Any  # type: ignore
    col = None  # type: ignore
    avg = count = sum = spark_max = spark_min = None  # type: ignore


class PipelineTransformationMixin:
    """Transformation methods for HealthcareDataPipeline."""

    async def _transform_data(self, extract_results: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Transform data with business logic and data quality improvements."""
        transformations = config.get("transformations", [])
        transformed_dfs = {}

        for source_name, extract_result in extract_results.items():
            if "dataframe" in extract_result:
                df = extract_result["dataframe"]

                for transformation in transformations:
                    df = await self._apply_transformation(df, transformation)

                transformed_dfs[source_name] = df

        merge_config = config.get("merge")
        if merge_config and len(transformed_dfs) > 1:
            merged_df = await self._merge_dataframes(transformed_dfs, merge_config)
            return {"merged_dataframe": merged_df, "source_dataframes": transformed_dfs}

        return {"transformed_dataframes": transformed_dfs}

    async def _apply_transformation(self, df: SparkDF, transformation: Dict[str, Any]) -> SparkDF:
        """Apply specific transformation to DataFrame."""
        transform_type = transformation.get("type")

        if transform_type == "filter":
            condition = transformation.get("condition")
            return df.filter(condition)

        elif transform_type == "aggregate":
            group_by = transformation.get("group_by")
            aggregations = transformation.get("aggregations", [])

            df_grouped = df.groupBy(group_by)
            for agg_item in aggregations:
                agg_type = agg_item.get("type")
                column = agg_item.get("column")
                alias = agg_item.get("alias")

                if agg_type == "sum":
                    df_grouped = df_grouped.agg(sum(col(column)).alias(alias))
                elif agg_type == "count":
                    df_grouped = df_grouped.agg(count(column).alias(alias))
                elif agg_type == "avg":
                    df_grouped = df_grouped.agg(avg(col(column)).alias(alias))
                elif agg_type == "max":
                    df_grouped = df_grouped.agg(spark_max(col(column)).alias(alias))
                elif agg_type == "min":
                    df_grouped = df_grouped.agg(spark_min(col(column)).alias(alias))

            return df_grouped

        elif transform_type == "join":
            join_df = transformation.get("dataframe")
            join_condition = transformation.get("condition")
            join_type = transformation.get("join_type", "inner")
            return df.join(join_df, join_condition, join_type)

        elif transform_type == "clean":
            df = df.dropDuplicates()

            null_handling = transformation.get("null_handling", {})
            for column, strategy in null_handling.items():
                if strategy == "drop":
                    df = df.filter(col(column).isNotNull())
                elif strategy == "default":
                    default_value = transformation.get("default_values", {}).get(column)
                    df = df.fillna({column: default_value})

            return df

        elif transform_type == "enrich":
            enrichments = transformation.get("enrichments", [])
            for enrichment in enrichments:
                system_col = enrichment.get("system_column")
                code_col = enrichment.get("code_column")
                target_col = enrichment.get("target_column")

                if system_col and code_col and target_col:
                    if hasattr(df, "withColumn"):
                        from pyspark.sql.functions import udf
                        from pyspark.sql.types import StringType

                        from backend.terminology import lookup_code

                        def lookup_display_fn(sys_val, code_val):
                            if not sys_val or not code_val:
                                return ""
                            res = lookup_code(str(sys_val), str(code_val))
                            return res.get("display", "") if res else ""

                        lookup_udf = udf(lookup_display_fn, StringType())
                        df = df.withColumn(target_col, lookup_udf(col(system_col), col(code_col)))
                    else:
                        import pandas as pd

                        from backend.terminology import lookup_code

                        if isinstance(df, pd.DataFrame):
                            df[target_col] = df.apply(
                                lambda row: (
                                    (lookup_code(str(row[system_col]), str(row[code_col])) or {}).get("display", "")
                                    if system_col in row
                                    and code_col in row
                                    and pd.notna(row[system_col])
                                    and pd.notna(row[code_col])
                                    else ""
                                ),
                                axis=1,
                            )
                        else:
                            import polars as pl

                            if isinstance(df, pl.DataFrame):

                                def local_lookup(struct):
                                    sys_val = struct.get(system_col)
                                    code_val = struct.get(code_col)
                                    if not sys_val or not code_val:
                                        return ""
                                    res = lookup_code(str(sys_val), str(code_val))
                                    return res.get("display", "") if res else ""

                                df = df.with_columns(
                                    pl.struct([system_col, code_col])
                                    .map_elements(local_lookup, return_dtype=pl.String)
                                    .alias(target_col)
                                )
            return df

        else:
            logger.warning("Unknown transformation type: %s", transform_type)
            return df

    async def _merge_dataframes(self, dataframes: Dict[str, SparkDF], merge_config: Dict[str, Any]) -> SparkDF:
        """Merge multiple DataFrames based on configuration."""
        merge_type = merge_config.get("type", "union")

        if merge_type == "union":
            result_df = None
            for df in dataframes.values():
                if result_df is None:
                    result_df = df
                else:
                    result_df = result_df.union(df)
            return result_df

        elif merge_type == "join":
            primary_df = list(dataframes.values())[0]
            for i, (name, df) in enumerate(list(dataframes.values())[1:], 1):
                join_condition = merge_config.get("join_conditions", {}).get(f"join_{i}")
                if join_condition:
                    primary_df = primary_df.join(df, join_condition, merge_config.get("join_type", "inner"))
            return primary_df

        else:
            raise ValueError(f"Unsupported merge type: {merge_type}")
