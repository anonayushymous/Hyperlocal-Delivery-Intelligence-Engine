#!/bin/bash
set -e

echo "========================================================"
echo " Starting Hyperlocal Delivery Intelligence Engine Pipeline"
echo "========================================================"

# 1. Wait for database availability
echo "Checking database connection on ${POSTGRES_HOST:-localhost}:${POSTGRES_PORT:-5432}..."
while ! nc -z "${POSTGRES_HOST:-localhost}" "${POSTGRES_PORT:-5432}"; do
  echo "Database is not reachable yet. Sleeping 2 seconds..."
  sleep 2
done
echo "PostgreSQL is reachable."

# 2. Run Database Initializer & Synthesizer
echo "Running Schema Initialization and Synthetic Data Ingestion (db_loader.py)..."
python db_loader.py

# 3. Execute Statistical Analytics Modules
if [ -f "./analytics/ab_testing.py" ]; then
    echo "Running A/B Experiment Analysis..."
    python ./analytics/ab_testing.py
fi

if [ -f "./analytics/anomaly_detection.py" ]; then
    echo "Running Anomaly Detection Engine..."
    python ./analytics/anomaly_detection.py
fi

echo "========================================================"
echo " Pipeline execution completed successfully."
echo " Launching Streamlit Dashboard on port 8501..."
echo "========================================================"

exec streamlit run app.py --server.port=8501 --server.address=0.0.0.0