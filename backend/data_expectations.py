"""
Data Expectations — Lightweight Data Quality Engine
===================================================
A Great Expectations-compatible schema and statistics validation framework
for cleaning, preprocessing, and model ingestion boundary checks.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd

logger = logging.getLogger(__name__)

VALIDATION_RESULTS_DIR = Path("data/validation_results")

@dataclass
class Expectation:
    expectation_type: str
    column: Optional[str] = None
    kwargs: Dict[str, Any] = field(default_factory=dict)
    severity: str = "WARNING"  # WARNING, CRITICAL

@dataclass
class ExpectationSuite:
    suite_name: str
    dataset_name: str
    expectations: List[Expectation] = field(default_factory=list)

@dataclass
class ValidationResult:
    success: bool
    expectation: Expectation
    observed_value: Any
    message: str

@dataclass
class SuiteValidationReport:
    suite_name: str
    dataset_name: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    success: bool = True
    success_rate: float = 1.0
    results: List[Dict[str, Any]] = field(default_factory=list)

class ExpectationRunner:
    """Evaluates data suites and registers quality outcomes to local validation logs."""

    def __init__(self) -> None:
        self._suites: Dict[str, ExpectationSuite] = {}
        VALIDATION_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        self._setup_default_suites()

    def create_suite(self, suite_name: str, dataset_name: str) -> ExpectationSuite:
        """Instantiates a new suite container."""
        suite = ExpectationSuite(suite_name=suite_name, dataset_name=dataset_name)
        self._suites[suite_name] = suite
        return suite

    def add_expectation(self, suite_name: str, expectation: Expectation) -> None:
        """Appends an expectation validation definition to a suite."""
        suite = self._suites.get(suite_name)
        if not suite:
            raise ValueError(f"Suite {suite_name} does not exist.")
        suite.expectations.append(expectation)

    def validate(self, suite_name: str, data: Union[List[Dict[str, Any]], pd.DataFrame], chunk_size: int = 5000) -> SuiteValidationReport:
        """Validates input records or DataFrame against a registered suite."""
        suite = self._suites.get(suite_name)
        if not suite:
            raise ValueError(f"Suite {suite_name} not found.")

        report = SuiteValidationReport(suite_name=suite_name, dataset_name=suite.dataset_name)
        results: List[ValidationResult] = []

        is_record_list = isinstance(data, list)
        total_rows = len(data)
        if total_rows == 0:
            report.success = False
            report.success_rate = 0.0
            report.results.append({
                "success": False,
                "message": "Dataset is empty. Cannot run validations.",
                "severity": "CRITICAL"
            })
            self._save_report(report)
            return report

        # Check if the dataset size warrants chunked validation to be memory-safe
        use_chunked = total_rows > chunk_size
        df = None if use_chunked else pd.DataFrame(data) if is_record_list else data

        for expectation in suite.expectations:
            if use_chunked:
                res = self._run_chunked_expectation(data, expectation, chunk_size=chunk_size)
            else:
                assert df is not None
                res = self._run_single_expectation(df, expectation)
            results.append(res)

        success_count = sum(1 for r in results if r.success)
        total_count = len(results)

        report.success = success_count == total_count
        report.success_rate = success_count / total_count if total_count > 0 else 1.0
        report.results = [
            {
                "success": r.success,
                "observed": r.observed_value,
                "message": r.message,
                "expectation_type": r.expectation.expectation_type,
                "column": r.expectation.column,
                "severity": r.expectation.severity
            }
            for r in results
        ]

        self._save_report(report)
        return report

    def _run_single_expectation(self, df: pd.DataFrame, exp: Expectation) -> ValidationResult:
        t = exp.expectation_type
        col = exp.column
        kwargs = exp.kwargs

        if t == "expect_column_to_exist":
            exists = col in df.columns
            return ValidationResult(
                success=exists,
                expectation=exp,
                observed_value=list(df.columns),
                message=f"Column '{col}' exists" if exists else f"Column '{col}' is missing"
            )

        if col not in df.columns:
            return ValidationResult(
                success=False,
                expectation=exp,
                observed_value=None,
                message=f"Evaluation column '{col}' missing from data."
            )

        series = df[col]

        if t == "expect_column_values_not_null":
            null_count = int(series.isnull().sum())
            success = null_count == 0
            return ValidationResult(
                success=success,
                expectation=exp,
                observed_value=f"{null_count} nulls",
                message=f"All values in '{col}' are non-null" if success else f"Found {null_count} nulls in '{col}'"
            )

        elif t == "expect_column_values_in_set":
            allowed = set(kwargs.get("value_set", []))
            invalid_series = series[~series.isin(allowed)]
            success = invalid_series.empty
            return ValidationResult(
                success=success,
                expectation=exp,
                observed_value=list(invalid_series.unique()[:5]) if not success else [],
                message=f"All values in '{col}' are within the permitted set" if success else f"Found invalid values in '{col}'"
            )

        elif t == "expect_column_values_between":
            min_val = kwargs.get("min_value")
            max_val = kwargs.get("max_value")

            # Filter non-null to avoid null issues in range comparisons
            non_null = series.dropna()
            out_of_bounds = pd.Series()
            if min_val is not None:
                out_of_bounds = non_null[non_null < min_val]
            if max_val is not None:
                out_of_bounds = pd.concat([out_of_bounds, non_null[non_null > max_val]])

            success = out_of_bounds.empty
            observed = f"Range: [{non_null.min()}, {non_null.max()}]" if not non_null.empty else "N/A"
            return ValidationResult(
                success=success,
                expectation=exp,
                observed_value=observed,
                message=f"All values in '{col}' are between {min_val} and {max_val}" if success else f"Found values in '{col}' outside [{min_val}, {max_val}]"
            )

        elif t == "expect_column_mean_between":
            min_mean = kwargs.get("min_value")
            max_mean = kwargs.get("max_value")
            mean_val = float(series.mean())
            success = True
            if min_mean is not None and mean_val < min_mean:
                success = False
            if max_mean is not None and mean_val > max_mean:
                success = False
            return ValidationResult(
                success=success,
                expectation=exp,
                observed_value=mean_val,
                message=f"Mean of '{col}' is {mean_val:.2f} (expected [{min_mean}, {max_mean}])"
            )

        elif t == "expect_table_row_count_between":
            min_rows = kwargs.get("min_value", 0)
            max_rows = kwargs.get("max_value", 100000000)
            row_count = len(df)
            success = min_rows <= row_count <= max_rows
            return ValidationResult(
                success=success,
                expectation=exp,
                observed_value=row_count,
                message=f"Row count {row_count} is between {min_rows} and {max_rows}"
            )

        elif t == "expect_column_values_to_match_regex":
            pattern = kwargs.get("regex", "")
            regex = re.compile(pattern)
            invalid_matches = series.dropna().astype(str).apply(lambda x: not bool(regex.match(x)))
            success = not invalid_matches.any()
            return ValidationResult(
                success=success,
                expectation=exp,
                observed_value=f"{invalid_matches.sum()} violations",
                message=f"All values in '{col}' match expression '{pattern}'"
            )

        elif t == "expect_column_unique_value_count_between":
            min_val = kwargs.get("min_value", 0)
            max_val = kwargs.get("max_value", 1000000)
            unique_count = int(series.nunique())
            success = min_val <= unique_count <= max_val
            return ValidationResult(
                success=success,
                expectation=exp,
                observed_value=unique_count,
                message=f"Unique value count is {unique_count} (expected [{min_val}, {max_val}])"
            )

        return ValidationResult(
            success=True,
            expectation=exp,
            observed_value=None,
            message="Unrecognized expectation type, skipped validation."
        )

    def _run_chunked_expectation(
        self,
        data: Union[List[Dict[str, Any]], pd.DataFrame],
        exp: Expectation,
        chunk_size: int = 5000,
    ) -> ValidationResult:
        t = exp.expectation_type
        col = exp.column
        kwargs = exp.kwargs
        is_record_list = isinstance(data, list)
        total_rows = len(data)
        if is_record_list:
            columns = list(dict.fromkeys(key for record in data for key in record))
        else:
            columns = list(data.columns)

        if t == "expect_column_to_exist":
            exists = col in columns
            return ValidationResult(
                success=exists,
                expectation=exp,
                observed_value=columns,
                message=f"Column '{col}' exists" if exists else f"Column '{col}' is missing"
            )

        if t == "expect_table_row_count_between":
            min_rows = kwargs.get("min_value", 0)
            max_rows = kwargs.get("max_value", 100000000)
            success = min_rows <= total_rows <= max_rows
            return ValidationResult(
                success=success,
                expectation=exp,
                observed_value=total_rows,
                message=f"Row count {total_rows} is between {min_rows} and {max_rows}"
            )

        if col not in columns:
            return ValidationResult(
                success=False,
                expectation=exp,
                observed_value=None,
                message=f"Evaluation column '{col}' missing from data."
            )

        null_count = 0
        invalid_values = set()
        out_of_bounds_count = 0
        min_val = None
        max_val = None
        running_sum = 0.0
        running_count = 0
        unique_values = set()
        regex_violations = 0

        for start in range(0, total_rows, chunk_size):
            if is_record_list:
                chunk = pd.DataFrame(data[start:start + chunk_size])
            else:
                chunk = data.iloc[start:start + chunk_size]
            if col in chunk.columns:
                series = chunk[col]
            else:
                series = pd.Series([None] * len(chunk), index=chunk.index, dtype=object)

            if t == "expect_column_values_not_null":
                null_count += int(series.isnull().sum())

            elif t == "expect_column_values_in_set":
                allowed = set(kwargs.get("value_set", []))
                invalid_series = series[~series.isin(allowed)]
                if not invalid_series.empty:
                    invalid_values.update(invalid_series.unique())

            elif t == "expect_column_values_between":
                min_limit = kwargs.get("min_value")
                max_limit = kwargs.get("max_value")
                non_null = series.dropna()
                if not non_null.empty:
                    if min_val is None or non_null.min() < min_val:
                        min_val = non_null.min()
                    if max_val is None or non_null.max() > max_val:
                        max_val = non_null.max()
                    if min_limit is not None:
                        out_of_bounds_count += int((non_null < min_limit).sum())
                    if max_limit is not None:
                        out_of_bounds_count += int((non_null > max_limit).sum())

            elif t == "expect_column_mean_between":
                non_null = series.dropna()
                running_sum += float(non_null.sum())
                running_count += int(non_null.count())

            elif t == "expect_column_values_to_match_regex":
                import re
                pattern = kwargs.get("regex", "")
                regex = re.compile(pattern)
                invalid_matches = series.dropna().astype(str).apply(lambda x: not bool(regex.match(x)))
                regex_violations += int(invalid_matches.sum())

            elif t == "expect_column_unique_value_count_between":
                unique_values.update(series.dropna().unique())

        if t == "expect_column_values_not_null":
            success = null_count == 0
            return ValidationResult(
                success=success,
                expectation=exp,
                observed_value=f"{null_count} nulls",
                message=f"All values in '{col}' are non-null" if success else f"Found {null_count} nulls in '{col}'"
            )

        elif t == "expect_column_values_in_set":
            success = len(invalid_values) == 0
            return ValidationResult(
                success=success,
                expectation=exp,
                observed_value=list(invalid_values)[:5] if not success else [],
                message=f"All values in '{col}' are within the permitted set" if success else f"Found invalid values in '{col}'"
            )

        elif t == "expect_column_values_between":
            success = out_of_bounds_count == 0
            observed = f"Range: [{min_val}, {max_val}]" if min_val is not None else "N/A"
            min_limit = kwargs.get("min_value")
            max_limit = kwargs.get("max_value")
            return ValidationResult(
                success=success,
                expectation=exp,
                observed_value=observed,
                message=f"All values in '{col}' are between {min_limit} and {max_limit}" if success else f"Found values in '{col}' outside [{min_limit}, {max_limit}]"
            )

        elif t == "expect_column_mean_between":
            min_mean = kwargs.get("min_value")
            max_mean = kwargs.get("max_value")
            mean_val = running_sum / running_count if running_count > 0 else 0.0
            success = True
            if min_mean is not None and mean_val < min_mean:
                success = False
            if max_mean is not None and mean_val > max_mean:
                success = False
            return ValidationResult(
                success=success,
                expectation=exp,
                observed_value=mean_val,
                message=f"Mean of '{col}' is {mean_val:.2f} (expected [{min_mean}, {max_mean}])"
            )

        elif t == "expect_column_values_to_match_regex":
            pattern = kwargs.get("regex", "")
            success = regex_violations == 0
            return ValidationResult(
                success=success,
                expectation=exp,
                observed_value=f"{regex_violations} violations",
                message=f"All values in '{col}' match expression '{pattern}'"
            )

        elif t == "expect_column_unique_value_count_between":
            min_val_limit = kwargs.get("min_value", 0)
            max_val_limit = kwargs.get("max_value", 1000000)
            unique_count = len(unique_values)
            success = min_val_limit <= unique_count <= max_val_limit
            return ValidationResult(
                success=success,
                expectation=exp,
                observed_value=unique_count,
                message=f"Unique value count is {unique_count} (expected [{min_val_limit}, {max_val_limit}])"
            )

        return ValidationResult(
            success=True,
            expectation=exp,
            observed_value=None,
            message="Unrecognized expectation type, skipped validation."
        )


    def _save_report(self, report: SuiteValidationReport) -> None:
        """Persists validation report to JSON."""
        file_path = VALIDATION_RESULTS_DIR / f"{report.suite_name}_latest.json"
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(asdict(report), f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error("Failed to write validation report: %s", e)

    def get_validation_results(self, suite_name: str) -> Optional[Dict[str, Any]]:
        """Reads the latest validation report from disk."""
        file_path = VALIDATION_RESULTS_DIR / f"{suite_name}_latest.json"
        if not file_path.exists():
            return None
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def _setup_default_suites(self) -> None:
        """Seeds standard expectations for demographics, labs, and vitals datasets."""
        # 1. Patient Demographics
        self.create_suite("patient_demographics", "patient_accounts")
        self.add_expectation("patient_demographics", Expectation("expect_column_to_exist", "username", severity="CRITICAL"))
        self.add_expectation("patient_demographics", Expectation("expect_column_values_not_null", "username", severity="CRITICAL"))
        self.add_expectation("patient_demographics", Expectation("expect_column_values_to_match_regex", "email", {"regex": r"^[^@]+@[^@]+\.[^@]+$"}))

        # 2. Lab Results
        self.create_suite("lab_results", "diagnostic_results")
        self.add_expectation("lab_results", Expectation("expect_column_to_exist", "result_value", severity="CRITICAL"))
        self.add_expectation("lab_results", Expectation("expect_column_values_not_null", "result_value", severity="CRITICAL"))

        # 3. Vitals
        self.create_suite("vitals", "vital_observations")
        self.add_expectation("vitals", Expectation("expect_column_to_exist", "heart_rate"))
        self.add_expectation("vitals", Expectation("expect_column_values_between", "heart_rate", {"min_value": 20, "max_value": 250}))
        self.add_expectation("vitals", Expectation("expect_column_values_between", "temperature", {"min_value": 30.0, "max_value": 45.0}))

# Global instance
expectation_runner = ExpectationRunner()
