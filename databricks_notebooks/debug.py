from pyspark.sql import SparkSession
spark = SparkSession.builder.getOrCreate()
df = spark.sql("SHOW VOLUMES IN apex.default")
for row in df.collect():
    print(f"VOLUME: {row.volume_name}")
