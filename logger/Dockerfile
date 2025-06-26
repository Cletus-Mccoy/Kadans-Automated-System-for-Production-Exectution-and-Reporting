FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
COPY postgres/schemaGeneration.py postgres/tagList_export.csv /app/
RUN chmod +x start.sh
CMD ["/bin/sh", "-c", "./start.sh"]
