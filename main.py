import psycopg2
import csv
import time
import subprocess


# collect data every 1ms
SAMPLE_FREQ = 0.001


# adapted from https://pgdash.io/blog/essential-postgres-monitoring-part3.html
table_growth_query = """
SELECT schemaname || '.' || relname AS table_name,
       pg_table_size(schemaname || '.' || relname)
  FROM pg_stat_user_tables
  ORDER BY table_name;
"""


def get_csv_header(cur):
    cur.execute(table_growth_query)
    return ["ds"] + [row[0] for row in cur.fetchall()]


if __name__ == '__main__':
    workload_name = "tpcc"

    # remove previous data
    subprocess.run(["sudo", "-u", "postgres", "psql", "-c", "DROP DATABASE IF EXISTS benchbase;"])
    subprocess.run(["sudo", "-u", "postgres", "psql", "-c", "CREATE DATABASE benchbase;"])

    # turn off autovacuum
    subprocess.run(["sudo", "bash", "-c", "\"echo 'autovacuum = off' >> /etc/postgresql/14/main/postgresql.conf\""])
    subprocess.run(["sudo", "service", "postgresql", "restart"])

    conn = psycopg2.connect(database="benchbase", user="project1user", password="project1pass", host="localhost",
                            port="5432")

    subprocess.run(['java', '-jar', 'benchbase.jar', '-b', 'tpcc', '-c', '/home/ubuntu/benchbase/target/benchbase-postgres/config/postgres/sample_tpcc_config.xml', '--create=true', '--load=true'])
    cur = conn.cursor()
    headers = get_csv_header(cur)
    cur.execute(table_growth_query)
    print(cur.fetchall())
    num_cols = len(headers)
    with open(f"{workload_name}_table_growth.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        benchbase = subprocess.Popen(['java', '-jar', 'benchbase.jar', '-b', 'tpcc', '-c', '/home/ubuntu/benchbase/target/benchbase-postgres/config/postgres/sample_tpcc_config.xml', '--execute=true'])
        while benchbase.poll() is None:
            cur.execute(table_growth_query)
            row = [time.time()] + [row[1] for row in cur.fetchall()]
            writer.writerow(row)
            time.sleep(SAMPLE_FREQ)

