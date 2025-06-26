FROM apache/superset:latest


USER root

RUN /app/.venv/bin/python -m ensurepip --upgrade && \
    /app/.venv/bin/python -m pip install --no-cache-dir --upgrade pip && \
    /app/.venv/bin/python -m pip install --no-cache-dir psycopg2-binary

COPY requirements.txt .
RUN /app/.venv/bin/python -m pip install -r requirements.txt

USER superset