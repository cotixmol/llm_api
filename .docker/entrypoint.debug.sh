#!/usr/bin/env bash
set -e

python -m debugpy \
       --listen 0.0.0.0:5678 \
       --wait-for-client \
       -m uvicorn app:app \
         --host 0.0.0.0 \
         --port 8002 \
         --reload