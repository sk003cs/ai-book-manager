#!/bin/sh

# File containing environment variables
filename=".env.dev"

echo "Exporting the variables from the $filename file"
set -a
. ./$filename
set +a

echo "Printing environment variables and paths for debugging"
echo $PATH
pipenv --venv
pipenv graph

echo "Starting Gunicorn"
# Activate the pipenv shell and run gunicorn
pipenv run gunicorn -w 9 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0 --log-level debug --timeout 90
