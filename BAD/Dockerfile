FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if any needed (e.g. for potential future extensions)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Set PYTHONPATH
ENV PYTHONPATH=/app

# Command to run (can be overridden, but this is the default for this bot)
CMD ["python3", "src/bridge/tickets_assistant.py"]
