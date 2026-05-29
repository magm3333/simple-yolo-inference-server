FROM python:3.9-slim

# Install minimal system dependencies for OpenCV and basic functionality
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*



WORKDIR /app

# Install Python dependencies with enhanced timeout and retry handling
# Copy requirements first to leverage Docker cache for faster rebuilds when only code changes
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --default-timeout=1000 --retries 10 -r requirements.txt


COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]