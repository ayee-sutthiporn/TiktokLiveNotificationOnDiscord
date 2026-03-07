FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY start.py .

# Force Python's stdout and stderr to be unbuffered so logs show up immediately in Docker
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "start.py"]
