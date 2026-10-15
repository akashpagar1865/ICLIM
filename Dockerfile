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
# Run as a non-root user
# Create a dedicated system user and give it the app folder,
# including logs/ and models/ so Docker volumes start out
# owned by this user.
# =====================================================
RUN useradd --system --uid 10001 --user-group --no-create-home iclim \
    && mkdir -p /app/logs /app/models \
    && chown -R iclim:iclim /app

USER iclim

# =====================================================
# Clean shutdown
# `docker stop` sends this signal. The agent already exits
# cleanly on Ctrl+C (SIGINT), so use it instead of SIGTERM,
# which Python ignores when it is the container's main process
# (that is what caused exit code 137).
# =====================================================
STOPSIGNAL SIGINT

# =====================================================
# Default Startup Command
# Launch the realtime monitoring agent.
# =====================================================
CMD ["python", "-m", "agents.realtime_anomaly_agent"]