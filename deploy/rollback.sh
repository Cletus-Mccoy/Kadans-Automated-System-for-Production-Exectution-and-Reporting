#!/bin/bash
TAG=$1
git checkout tags/$TAG
docker-compose up -d --force-recreate
