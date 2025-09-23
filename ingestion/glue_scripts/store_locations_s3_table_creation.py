from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("store_location_glue_table_creation") \
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
    .config("spark.sql.defaultCatalog", "s3_rest_catalog") \
    .config("spark.sql.catalog.s3_rest_catalog", "org.apache.iceberg.spark.SparkCatalog") \
    .config("spark.sql.catalog.s3_rest_catalog.type", "rest") \
    .config("spark.sql.catalog.s3_rest_catalog.uri", "https://s3tables.us-east-2.amazonaws.com/iceberg") \
    .config("spark.sql.catalog.s3_rest_catalog.warehouse", "arn:aws:s3tables:us-east-2:487577641151:bucket/iceberg-tables") \
    .config("spark.sql.catalog.s3_rest_catalog.rest.sigv4-enabled", "true") \
    .config("spark.sql.catalog.s3_rest_catalog.rest.signing-name", "s3tables") \
    .config("spark.sql.catalog.s3_rest_catalog.rest.signing-region", "us-east-2") \
    .config('spark.sql.catalog.s3_rest_catalog.io-impl','org.apache.iceberg.aws.s3.S3FileIO') \
    .config('spark.sql.catalog.s3_rest_catalog.rest-metrics-reporting-enabled','false') \
    .getOrCreate() 

namespace = "inflation_price_tracker"
table = "store_location"

spark.sql(f"CREATE NAMESPACE IF NOT EXISTS {namespace}")
spark.sql(f"DESCRIBE NAMESPACE {namespace}").show()

spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {namespace}.{table} ( 
        store_id int
        , address_line1 string 
        , city string 
        , region string 
        , country_code string 
        , postal_code string 
        , retailer_name string 
        , parent_retailer_company_name string 
        , ingestion_datetime timestamp
    )
""")

# Read your existing data
df = spark.read.format("parquet").load("s3://inflation-price-tracker-production/ingestion/transformed/target/country=US/target_stores.parquet")

# Write to Iceberg format, creating the table in the Glue Data Catalog
df.writeTo(f"{namespace}.{table}") \
    .append()
    
   