#!/bin/bash
set -e
git checkout main
git pull origin main
docker-compose up -d --build
