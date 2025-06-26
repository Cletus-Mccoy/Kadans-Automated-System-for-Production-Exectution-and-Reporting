# TwinCAT PLC Logger - Docker Deployment

This project provides a scalable, zero-downtime logging infrastructure for collecting and storing TwinCAT PLC variables in PostgreSQL, with analysis via Superset (default) and admin access via pgAdmin. The stack is orchestrated using Docker Compose, and deployment is managed with git-based scripts for easy rollbacks.

## 🚀 Features

- 🐘 PostgreSQL for high-performance time-series logging
- 🐍 Python-based logger using `opcua` to connect to various PLC brands
- 📊 Superset for dashboards and visualization (default)
- 🔧 pgAdmin for DB admin access
- 🐳 Docker Compose orchestration
- 🛡 Git-based, rollback-safe deployment scripts
- ⚡ Environment-based configuration via `.env` file

---

## 📦 Stack Overview

| Component   | Description                                      |
|------------|--------------------------------------------------|
| logger     | Python app that subscribes to PLC variables via ADS |
| postgres   | Stores logged data                               |
| pgAdmin    | Web-based PostgreSQL admin tool                  |
| superset   | BI/dashboard tool for analysis (enabled by default) |
| metabase   | (Optional) BI/dashboard tool, currently disabled in compose |
| deploy.sh  | Deployment script with minimal downtime          |
| rollback.sh| Quick rollback to previous Git-tagged versions   |

---

## 🛠 Setup

### 1. Clone the repo

```bash
git clone https://your.git.repo/url.git
cd MES-v2
```

### 2. Configure .env

Create a `.env` file in the project root (see `.env` example below). This file is required and is not committed to git.

```ini
POSTGRES_USER=yourUsername
POSTGRES_PASSWORD=yourPassword
POSTGRES_DB=yourDatabaseName
POSTGRES_PORT=5432
PGADMIN_EMAIL=your@email.com
PGADMIN_PASSWORD=yourPgAdminPassword
PGADMIN_PORT=8080
SUPERSET_PORT=8088
SUPERSET_SECRET_KEY=yourSupersetSecretKey
```

### 3. Start Services

```bash
./deploy/deploy.sh
```

This will build and start all enabled services (PostgreSQL, pgAdmin, Superset, logger) using Docker Compose. The script will ensure you are on the latest `main` branch and pull updates before deploying.

---

## 🔁 Deployment & Rollback

### Production Deployment

```bash
./deploy/deploy.sh
```

This script checks out the `main` branch, pulls the latest changes, and (re)builds all containers with minimal downtime.

### Rollback

To roll back to a previous tagged version:

```bash
./deploy/rollback.sh v1.0.2
```

This checks out the specified git tag and recreates the containers.

---

## 🔎 Access

- **pgAdmin:** http://localhost:8080 (default credentials from `.env`)
- **Superset:** http://localhost:8088 (default admin: admin/admin)
- **Metabase:** http://localhost:3000 (if enabled in `docker-compose.yml`)
- **PostgreSQL:** exposed internally to logger and other containers only

---

## 📈 Data Table Example

```sql
CREATE TABLE variable_log (
  id SERIAL PRIMARY KEY,
  machine_name TEXT NOT NULL,
  variable_name TEXT NOT NULL,
  value TEXT,
  timestamp TIMESTAMPTZ DEFAULT now()
);
```

---

## 📄 Variable Management and Dynamic Schema

- All variables (including attributes) are defined in `logger/postgres/tagList_export.csv`.
- The schema generation script (`logger/postgres/schemaGeneration.py`) will automatically create or alter the `machine_data_log` table to match the CSV, adding new columns as needed.
- The mock OPC UA server (`logger/mock_opcua_server.py`) and the logger (`logger/dataAqcuisition.py`) both use this CSV for variable definitions, ensuring consistency across the stack.
- To add or remove variables/attributes, simply update the CSV and restart the stack.

## 🧠 Attribute-Aware Analytics

- Correlation and grouping in analytics are dynamic: any variable in the CSV with type `STRING` is used as a grouping attribute for correlation analysis.
- Example: If you add a new attribute (e.g., `BatchID,STRING`) to the CSV, it will automatically be included in grouping for correlation in Superset or other BI tools.

## 🔄 Example Data Flow

1. **Mock OPC UA Server** simulates all variables and attributes from the CSV.
2. **Logger** connects to the OPC UA server, reads all variables, and logs them to PostgreSQL.
3. **Schema Generation** ensures the database table matches the CSV, adding new columns as needed.
4. **Superset** and **pgAdmin** provide analytics and admin access to the logged data.

## 📝 Example Analytics Query
To analyze correlations by attribute (e.g., by `Color`):
```sql
SELECT * FROM correlation_matrix WHERE color = 'red';
```

## 🛠 Environment Variables (.env)
- `POSTGRES_USER` - Username for PostgreSQL
- `POSTGRES_PASSWORD` - Password for PostgreSQL
- `POSTGRES_DB` - Database name for PostgreSQL
- `POSTGRES_PORT` - Port for PostgreSQL (default: 5432)
- `PGADMIN_EMAIL` - Email for pgAdmin login
- `PGADMIN_PASSWORD` - Password for pgAdmin login
- `PGADMIN_PORT` - Port for pgAdmin (default: 8080)
- `SUPERSET_PORT` - Port for Superset (default: 8088)
- `SUPERSET_SECRET_KEY` - Secret key for Superset
- `METABASE_PORT` - Port for Metabase (optional, default: 3000)

## 🔄 Updating Variables
- To add a new variable or attribute, add it to `logger/postgres/tagList_export.csv` and restart the stack.
- The schema and mock server will update automatically.

## 💡 Support
For issues, feature requests, or contributions, please open an issue or pull request on the repository.

---

## 🧰 Future Enhancements

- Admin UI to manage variable registry
- CI/CD pipeline
- Dynamic variable subscriptions
- Enable/disable Metabase as needed

