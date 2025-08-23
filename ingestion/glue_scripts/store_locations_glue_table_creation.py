import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql import SparkSession
from awsglue.context import GlueContext
from awsglue.job import Job

spark = SparkSession.builder \
    .config("spark.sql.catalog.glue_catalog", "org.apache.iceberg.spark.SparkSessionCatalog") \
    .config("spark.sql.catalog.glue_catalog.warehouse", "s3://inflation-price-tracker-production/ingestion/iceberg/") \
    .config("spark.sql.catalog.glue_catalog.catalog-impl", "org.apache.iceberg.aws.glue.GlueCatalog") \
    .getOrCreate()

# Read your existing data
df = spark.read.format("parquet").load("s3://inflation-price-tracker-production/ingestion/transformed/target/country=US/target_stores.parquet")

# Write to Iceberg format, creating the table in the Glue Data Catalog
df.writeTo("glue_catalog.inflation_price_tracker.target_store_locations") \
    .option("path", "s3://inflation-price-tracker-production/ingestion/iceberg/inflation_price_tracker.db/target_store_locations/") \
    .createOrReplace()