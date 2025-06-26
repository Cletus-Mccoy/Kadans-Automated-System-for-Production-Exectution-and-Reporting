import os
import csv
import psycopg2

CSV_FILE = 'tagList_export.csv'
TABLE_NAME = 'machine_data_log'
COLUMN_PREFIX = 'm1_'  # your desired prefix

conn = psycopg2.connect(
    dbname=os.environ.get("POSTGRES_DB", "plclogger"),
    user=os.environ.get("POSTGRES_USER", "user"),
    password=os.environ.get("POSTGRES_PASSWORD", "password"),
    host=os.environ.get("POSTGRES_HOST", "db"),
    port=os.environ.get("POSTGRES_PORT", 5432)
)
cursor = conn.cursor()

# Define type map from PLC tags types to Postgres
type_map = {
    'INT': 'INTEGER',
    'BOOL': 'BOOLEAN',
    'REAL': 'REAL',
    'DINT': 'INTEGER',
    'STRING': 'TEXT'
}

# Read CSV and build columns from all variables
with open(CSV_FILE, newline='') as f:
    reader = csv.DictReader(f)
    columns = []
    for row in reader:
        var_name = row['Name'].replace('.', '_')  # Optional: sanitize
        col_name = f"{COLUMN_PREFIX}{var_name.lower()}"
        tc_type = row['Type'].upper()
        pg_type = type_map.get(tc_type, 'TEXT')  # Fallback to TEXT
        columns.append(f'"{col_name}" {pg_type}')

# Add a timestamp column
columns.insert(0, 'timestamp TIMESTAMPTZ DEFAULT now()')

# Add or alter columns if table already exists
for col in columns[1:]:  # skip timestamp
    col_name = col.split()[0].strip('"')
    col_type = col.split()[1]
    cursor.execute(f"ALTER TABLE {TABLE_NAME} ADD COLUMN IF NOT EXISTS {col_name} {col_type};")

# Build CREATE TABLE query (for first-time creation)
sql = f'CREATE TABLE IF NOT EXISTS {TABLE_NAME} (\n  ' + ',\n  '.join(columns) + '\n);'
cursor.execute(sql)
conn.commit()

print(f"Table `{TABLE_NAME}` created with {len(columns)-1} variable columns.")
cursor.close()
conn.close()
