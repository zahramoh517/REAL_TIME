import psycopg

conn = psycopg.connect(
    dbname="postgres",
    user="zahra",
    host="localhost",
    port=5432
)
db_connection = conn.cursor()
