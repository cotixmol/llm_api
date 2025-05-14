#################### BASE BUILD IMAGE ####################
# The heaviest part of the build is vllm, so we put everything it
# needs (tool‑chain + vllm itself) as early as possible.
FROM python:3.11.4-slim-bullseye AS base

# 1️⃣ System‑level build tools (needed before we touch vllm)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        ninja-build \
        libnuma-dev \
    && rm -rf /var/lib/apt/lists/*

# 2️⃣ Python package manager
RUN python -m pip install --upgrade pip

# 3️⃣ Heavy Python libs
ENV MAX_JOBS=2
RUN pip install --no-cache-dir vllm==0.8.2
RUN pip install --no-cache-dir --no-deps bertopic==0.16.2

WORKDIR /app
#################### BASE BUILD IMAGE ####################

#################### GPU REPORTS IMAGE ####################
# Everything from here down can be invalidated & rebuilt
# without ever recompiling vllm again.
FROM base AS gpu_reports

# Lightweight Python requirements for *this* repo
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && rm requirements.txt

# Debugger
RUN pip install --no-cache-dir debugpy

# Project code
COPY . .

ENTRYPOINT ["python", "app.py"]
#################### GPU REPORTS IMAGE ####################
