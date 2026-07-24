import importlib
import os
import sys
import types


def setup_airflow_mocks():
    """Mock the entire apache-airflow library dynamically to validate DAGs without installation"""
    # Create base modules
    airflow = types.ModuleType("airflow")
    airflow_models = types.ModuleType("airflow.models")
    airflow_operators = types.ModuleType("airflow.operators")
    airflow_operators_python = types.ModuleType("airflow.operators.python")
    airflow_operators_empty = types.ModuleType("airflow.operators.empty")
    airflow_providers = types.ModuleType("airflow.providers")
    airflow_providers_redis = types.ModuleType("airflow.providers.redis")
    airflow_providers_redis_hooks = types.ModuleType("airflow.providers.redis.hooks")
    airflow_providers_redis_hooks_redis = types.ModuleType("airflow.providers.redis.hooks.redis")
    airflow_providers_spark = types.ModuleType("airflow.providers.spark")
    airflow_providers_spark_operators = types.ModuleType("airflow.providers.spark.operators")
    airflow_providers_spark_operators_spark_submit = types.ModuleType("airflow.providers.spark.operators.spark_submit")
    airflow_sensors = types.ModuleType("airflow.sensors")
    airflow_sensors_sql = types.ModuleType("airflow.sensors.sql")

    # Stub class for DAG
    class MockDAG:
        def __init__(self, dag_id, *args, **kwargs):
            self.dag_id = dag_id
            self.tasks = []
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    # Stub class for Operators & Sensors supporting Airflow's shift operators (>> and <<) with lists
    class MockOperator:
        def __init__(self, task_id, *args, **kwargs):
            self.task_id = task_id
        def __rshift__(self, other):
            return other
        def __rrshift__(self, other):
            return self
        def __lshift__(self, other):
            return other
        def __rlshift__(self, other):
            return self

    # Stub class for Hooks
    class MockHook:
        def __init__(self, *args, **kwargs):
            pass

    # Assign classes to mocked modules
    airflow.DAG = MockDAG
    airflow_models.DAG = MockDAG
    airflow_operators_python.PythonOperator = MockOperator
    airflow_operators_python.BranchPythonOperator = MockOperator
    airflow_operators_empty.EmptyOperator = MockOperator
    airflow_providers_redis_hooks_redis.RedisHook = MockHook
    airflow_providers_spark_operators_spark_submit.SparkSubmitOperator = MockOperator
    airflow_sensors_sql.SqlSensor = MockOperator

    # Register in sys.modules
    sys.modules["airflow"] = airflow
    sys.modules["airflow.models"] = airflow_models
    sys.modules["airflow.operators"] = airflow_operators
    sys.modules["airflow.operators.python"] = airflow_operators_python
    sys.modules["airflow.operators.empty"] = airflow_operators_empty
    sys.modules["airflow.providers"] = airflow_providers
    sys.modules["airflow.providers.redis"] = airflow_providers_redis
    sys.modules["airflow.providers.redis.hooks"] = airflow_providers_redis_hooks
    sys.modules["airflow.providers.redis.hooks.redis"] = airflow_providers_redis_hooks_redis
    sys.modules["airflow.providers.spark"] = airflow_providers_spark
    sys.modules["airflow.providers.spark.operators"] = airflow_providers_spark_operators
    sys.modules["airflow.providers.spark.operators.spark_submit"] = airflow_providers_spark_operators_spark_submit
    sys.modules["airflow.sensors"] = airflow_sensors
    sys.modules["airflow.sensors.sql"] = airflow_sensors_sql

# Setup the mocks
setup_airflow_mocks()

def test_airflow_dags_compilation():
    """Verify that all Airflow DAGs import and compile without python syntax or logical errors"""
    dags_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "airflow", "dags")
    dag_files = [f for f in os.listdir(dags_dir) if f.endswith(".py") and f != "__init__.py"]

    # Add dags directory to python path for compilation imports
    sys.path.insert(0, dags_dir)

    print(f"Validating Airflow DAG files: {dag_files}")
    assert len(dag_files) > 0

    try:
        for fname in dag_files:
            module_name = fname.replace(".py", "")
            # Remove old reference if loaded
            sys.modules.pop(module_name, None)
            try:
                # Attempt to import/compile the DAG module
                importlib.import_module(module_name)
                print(f"SUCCESS: Compiled DAG file: {fname}")
            except Exception as e:
                raise AssertionError(f"Airflow DAG compilation failed for {fname}: {e}")
    finally:
        # Clean up path after complete validation
        sys.path.remove(dags_dir) if dags_dir in sys.path else None
