from pyspark.sql import SparkSession
spark = SparkSession.builder.getOrCreate()
try:
    spark.sql("CREATE VOLUME IF NOT EXISTS apex.default.telemetry")
    print("VOLUME CREATED SUCCESSFULLY!")
except Exception as e:
    print(f"FAILED TO CREATE VOLUME: {e}")
