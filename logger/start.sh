#!/bin/sh
# Start the mock OPC UA server in the background
python mock_opcua_server.py &
# Wait a bit to ensure the server is up
sleep 10
# Run schema generation and the logger
python schemaGeneration.py
python dataAqcuisition.py
