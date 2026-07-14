# =====================================================
# Base Image
# Official Python runtime on Debian Slim Linux.
# =====================================================
FROM python:3.12-slim

# =====================================================
# Working Directory
# All application files will live under /app.
# =====================================================
WORKDIR /app

# =====================================================
# Update PIP & Install Python Dependencies
# Copy requirements first to maximize Docker layer caching.
# =====================================================
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# =====================================================
# Copy Runtime Source Code
# =====================================================
COPY agents ./agents
COPY analysis ./analysis
COPY utils ./utils
COPY config ./config

# =====================================================
# Default Startup Command
# Launch the realtime monitoring agent.
# =====================================================
CMD ["python", "-m", "agents.realtime_anomaly_agent"]