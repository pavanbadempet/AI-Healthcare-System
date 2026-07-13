from backend import data_expectations
from backend.data_expectations import Expectation, ExpectationRunner
from backend.terminology import SNOMED_SYSTEM, lookup_code


def test_chunked_sparse_records_detect_column_and_missing_values(tmp_path, monkeypatch):
    monkeypatch.setattr(data_expectations, "VALIDATION_RESULTS_DIR", tmp_path)
    original_dataframe = data_expectations.pd.DataFrame

    def bounded_dataframe(data=None, *args, **kwargs):
        if isinstance(data, list):
            assert len(data) <= 2
        return original_dataframe(data, *args, **kwargs)

    monkeypatch.setattr(data_expectations.pd, "DataFrame", bounded_dataframe)
    runner = ExpectationRunner()
    runner.create_suite("sparse_records", "test_dataset")
    runner.add_expectation(
        "sparse_records",
        Expectation("expect_column_to_exist", "value"),
    )
    runner.add_expectation(
        "sparse_records",
        Expectation("expect_column_values_not_null", "value"),
    )

    report = runner.validate(
        "sparse_records",
        [{"other": 1}, {"value": 2}, {"value": 3}, {"value": 4}],
        chunk_size=2,
    )

    assert report.success is False
    assert report.results[0]["success"] is True
    assert report.results[1]["success"] is False
    assert report.results[1]["observed"] == "1 nulls"


def test_terminology_lookup_accepts_numeric_codes_and_none():
    expected_display = "Diabetes mellitus type 2"

    assert lookup_code(SNOMED_SYSTEM, 44054006)["display"] == expected_display
    assert lookup_code(SNOMED_SYSTEM, 44054006.0)["display"] == expected_display
    assert lookup_code(None, "44054006") is None
    assert lookup_code(SNOMED_SYSTEM, None) is None
