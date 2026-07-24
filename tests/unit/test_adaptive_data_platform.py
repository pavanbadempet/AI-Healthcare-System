from backend.data_engineering_platform import AdaptiveDataPlatformRouter, DataScaleEngine


def test_adaptive_router_embedded_mode():
    router = AdaptiveDataPlatformRouter(preferred_mode="embedded")
    engine = router.determine_engine(dataset_path_or_bytes=1000)
    assert engine == DataScaleEngine.DUCKDB_EMBEDDED


def test_adaptive_router_distributed_mode():
    router = AdaptiveDataPlatformRouter(preferred_mode="distributed")
    engine = router.determine_engine(dataset_path_or_bytes=1000)
    assert engine == DataScaleEngine.PYSPARK_DISTRIBUTED


def test_adaptive_router_auto_mode_small_scale():
    router = AdaptiveDataPlatformRouter(preferred_mode="auto")
    engine = router.determine_engine(dataset_path_or_bytes=1024 * 1024)  # 1 MB
    assert engine == DataScaleEngine.DUCKDB_EMBEDDED


def test_adaptive_router_auto_mode_large_scale():
    router = AdaptiveDataPlatformRouter(preferred_mode="auto")
    large_size = 60 * 1024 * 1024 * 1024  # 60 GB
    engine = router.determine_engine(dataset_path_or_bytes=large_size)
    assert engine == DataScaleEngine.PYSPARK_DISTRIBUTED
