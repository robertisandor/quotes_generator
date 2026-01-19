import psycopg2
import os
import json

def lambda_handler(event, context):
    db_host = "travel-homie.ctkzwlmanw56.us-east-2.rds.amazonaws.com"
    db_name = "travel_homie_db"
    db_user = "postgres"
    db_password = "testpassword"
    db_port = "5432"

    conn = None
    try:
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password,
            port=db_port
        )
        cur = conn.cursor()

        create_table_sql = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE
        );
        """
        cur.execute(create_table_sql)

        # cur.execute("INSERT INTO users (id, name, email) VALUES (%s, %s, %s);", (1, 'testname', 'testemail@gmail.com'))
        cur.execute("INSERT INTO users (id, name, email) VALUES (%s, %s, %s);", (2, 'testname2', 'testemail2@gmail.com'))
        conn.commit()

        # Example: Execute a SELECT query
        cur.execute("SELECT * FROM users;")
        rows = cur.fetchall()
        print(f"Query results: {rows}")

        cur.close()
        return {
            'statusCode': 200,
            'body': json.dumps({"message": "Successfully queried PostgreSQL."})
        }
    except Exception as e:
        print(f"Error connecting to or querying PostgreSQL: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({"error": f"{str(e)}"})
        }
    finally:
        if conn:
            conn.close()