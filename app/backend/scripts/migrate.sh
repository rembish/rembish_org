#!/bin/sh
# Migration script for Cloud Run Job
# Runs alembic migrations and exits

set -e

echo "Running database migrations..."
alembic upgrade head
echo "Migrations complete."
