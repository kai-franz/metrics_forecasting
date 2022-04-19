from distutils.command.config import config
import psycopg2
import csv
import time
import subprocess
import sys


# collect data every 1ms
SAMPLE_FREQ = 1


# adapted from https://pgdash.io/blog/essential-postgres-monitoring-part3.html
table_growth_query = """
  SELECT ut.schemaname || '.' || ut.relname AS table_name,
        pg_stat_all_tables.*,
       pg_table_size(ut.schemaname || '.' || ut.relname)
  FROM pg_stat_user_tables AS ut
  JOIN pg_stat_all_tables ON pg_stat_all_tables.schemaname = ut.schemaname AND pg_stat_all_tables.relname = ut.relname
  ORDER BY table_name;
"""


def get_csv_header(cur):
    cur.execute(table_growth_query)
    header= ["ds"] + [col[0] for col in cur.description ]
    print("header", header)
    return header

def xmledit(param, value, fname):
    subprocess.run(["xmlstarlet", "edit", "--inplace", "--update", param, "--value", value, fname])

# workloads = ['voter', 'tatp']
workloads = ['tpcc', 'smallbank']
scale_factors = [50, 100]
work_times = [int(1*60*60)]

if __name__ == '__main__':
    for scale_factor in scale_factors:
        for workload in workloads:
            for work_time in work_times:
                workload_name = workload
                config_file = f"config/postgres/sample_{workload_name}_config.xml"
                experiment_name = f"noautovac_{workload_name}_scale_{scale_factor}_worktime_{work_time}_samplefreq_{SAMPLE_FREQ}_tsizeAnddeadtuple"
                benchmark = workload

                subprocess.run(["sudo", "service", "postgresql", "restart"])

                xmledit('/parameters/username', 'project1user', config_file)
                xmledit('/parameters/password', 'project1pass', config_file)
                xmledit('/parameters/scalefactor', str(scale_factor), config_file)
                xmledit('/parameters/works/work/time', str(work_time), config_file)

                print("Running " + experiment_name)

                # remove previous data
                subprocess.run(["sudo", "-u", "postgres", "psql", "-c", "DROP DATABASE IF EXISTS benchbase;"])
                subprocess.run(["sudo", "-u", "postgres", "psql", "-c", "CREATE DATABASE benchbase;"])

                # turn off autovacuum
                # subprocess.run(["sudo", "bash", "-c", "\"echo 'autovacuum = off' >> /etc/postgresql/14/main/postgresql.conf\""])
                

                conn = psycopg2.connect(database="benchbase", user="project1user", password="project1pass", host="localhost",
                                        port="5432")

                subprocess.run(['java', '-jar', 'benchbase.jar', '-b', benchmark, '-c', config_file, '--create=true', '--load=true'])
                cur = conn.cursor()
                cur.execute(table_growth_query)
                
                headers = get_csv_header(cur)
                # print(cur.fetchall())
                # num_cols = len(headers)
                with open(f"{experiment_name}.csv", "w") as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    benchbase = subprocess.Popen(['java', '-jar', 'benchbase.jar', '-b', benchmark, '-c', config_file, '--execute=true'])
                    while benchbase.poll() is None:
                        ctime = time.time()
                        cur.execute(table_growth_query)

                        for res_row in cur.fetchall():                        
                            row = [ctime] + [r for r in res_row]
                            writer.writerow(row)
                        time.sleep(SAMPLE_FREQ)

