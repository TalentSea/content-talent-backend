FROM python:3.12-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install wait-for-it dependencies and download the script
ADD https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh /usr/local/bin/wait-for-it
RUN apt-get update && \
    apt-get install -y --no-install-recommends netcat-openbsd && \
    rm -rf /var/lib/apt/lists/* && \
    chmod +x /usr/local/bin/wait-for-it

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Wait for Postgres, then start Uvicorn
CMD ["wait-for-it", "host.docker.internal:5432", "--timeout=30", "--strict", "--", \
     "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
