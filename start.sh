#!/bin/bash
PORT=${PORT:-5000}
exec gunicorn --bind 0.0.0.0:$PORT --timeout 120 app:app
