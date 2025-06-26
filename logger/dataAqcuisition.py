import os
import csv
import yaml
from opcua import Client
import psycopg2
import threading
import time
import pandas as pd
from sqlalchemy import create_engine

def generate_config_from_csv(csv_path="postgres/tagList_export.csv", config_path="config.yaml", nodeids_file="/app/nodeids.yaml"):
    # Read actual NodeIds from file
    try:
        with open(nodeids_file) as f:
            nodeids = yaml.safe_load(f)
    except Exception:
        nodeids = {}
    machines = [
        {
            "name": "machine_A",
            "opcua_url": "opc.tcp://localhost:4840",
            "variables": []
        }
    ]
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            var_name = row["Name"]
            var_type = row["Type"]
            node_id = nodeids.get(var_name, f"ns=2;s={var_name}")
            machines[0]["variables"].append({
                "name": var_name,
                "node_id": node_id,
                "type": var_type,
                "trigger": "on_cycle"
            })
    with open(config_path, "w") as f:
        yaml.dump({"machines": machines}, f)

def load_config(path="config.yaml"):
    with open(path) as f:
        return yaml.safe_load(f)

def connect_postgres():
    return psycopg2.connect(
        dbname=os.environ.get("POSTGRES_DB", "plclogger"),
        user=os.environ.get("POSTGRES_USER", "user"),
        password=os.environ.get("POSTGRES_PASSWORD", "password"),
        host=os.environ.get("POSTGRES_HOST", "db"),
        port=os.environ.get("POSTGRES_PORT", 5432)
    )

def monitor_machine(machine_cfg, db_conn, table_name="machine_data_log"):
    client = Client(machine_cfg["opcua_url"])
    client.connect()
    cursor = db_conn.cursor()
    state = {}

    for var in machine_cfg["variables"]:
        node = client.get_node(var["node_id"])
        state[var["name"]] = node.get_value()

    if any(v["trigger"] == "on_cycle" for v in machine_cfg["variables"]):
        while True:
            # Gather all values for this cycle
            values = {}
            for var in machine_cfg["variables"]:
                if var["trigger"] == "on_cycle":
                    node = client.get_node(var["node_id"])
                    val = node.get_value()
                    values[var["name"]] = val
            # Log all variables in one row
            log(cursor, table_name, machine_cfg["name"], values)
            time.sleep(1)

def log(cursor, table_name, machine, values):
    # Get types for each variable from CSV
    type_map = {}
    with open("postgres/tagList_export.csv", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            type_map[row["Name"]] = row["Type"].upper()
    
    col_names = [f'm1_{k.lower()}'.replace('.', '_') for k in values.keys()]
    placeholders = ', '.join(['%s'] * len(values))
    # Cast values to correct type
    casted_values = []
    for k, v in values.items():
        typ = type_map.get(k, "STRING")
        if typ == "INT" or typ == "DINT":
            try:
                casted_values.append(int(v))
            except Exception:
                casted_values.append(None)
        elif typ == "REAL":
            try:
                casted_values.append(float(v))
            except Exception:
                casted_values.append(None)
        elif typ == "BOOL":
            casted_values.append(bool(v))
        else:
            casted_values.append(str(v))
    sql = f"INSERT INTO {table_name} (timestamp, {', '.join(col_names)}) VALUES (now(), {placeholders})"
    try:
        cursor.execute(sql, tuple(casted_values))
        cursor.connection.commit()
    except Exception as e:
        cursor.connection.rollback()
        print(f"Failed to log variables {list(values.keys())}: {e}")

def correlation_worker(interval_seconds=300):
    # Dynamically determine attribute columns from CSV
    attr_types = ["STRING"]
    csv_path = "postgres/tagList_export.csv"
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        attribute_columns = [row["Name"].lower() for row in reader if row["Type"].upper() in attr_types]

    def run():
        while True:
            try:
                print("[Correlation] Updating correlation matrix...")
                engine = create_engine(
                    f"postgresql://{os.environ.get('POSTGRES_USER', 'user')}:{os.environ.get('POSTGRES_PASSWORD', 'password')}@{os.environ.get('POSTGRES_HOST', 'db')}:{os.environ.get('POSTGRES_PORT', 5432)}/{os.environ.get('POSTGRES_DB', 'plclogger')}"
                )
                df = pd.read_sql("SELECT * FROM machine_data_log", engine)

                group_attrs = [col for col in attribute_columns if col in df.columns]
                results = []

                if not group_attrs:
                    numeric = df.select_dtypes(include="number").dropna()
                    if len(numeric) >= 2:
                        corr = numeric.corr().stack().reset_index()
                        corr.columns = ["var_x", "var_y", "correlation"]
                        corr["group"] = "ALL"
                        results.append(corr)
                else:
                    for values, group_df in df.groupby(group_attrs):
                        numeric = group_df.select_dtypes(include="number").dropna()
                        if len(numeric) >= 2:
                            corr = numeric.corr().stack().reset_index()
                            corr.columns = ["var_x", "var_y", "correlation"]
                            for i, attr in enumerate(group_attrs):
                                corr[attr] = values[i]
                            results.append(corr)

                if results:
                    corr_df = pd.concat(results, ignore_index=True)
                    corr_df.to_sql("correlation_matrix", engine, if_exists="replace", index=False)
                    print("[Correlation] Matrix updated successfully.")
                else:
                    print("[Correlation] No data available for correlation.")

            except Exception as e:
                print(f"[Correlation] Error: {e}")

            time.sleep(interval_seconds)

    t = threading.Thread(target=run, daemon=True)
    t.start()

def main():
    generate_config_from_csv()
    config = load_config()
    db_conn = connect_postgres()
    threads = []
    correlation_worker(interval_seconds=300)  # Run every 5 minutes

    for machine in config["machines"]:
        t = threading.Thread(target=monitor_machine, args=(machine, db_conn))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

if __name__ == "__main__":
    main()
