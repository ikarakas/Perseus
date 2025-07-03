FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /generator

# Copy requirements and install Python dependencies
COPY requirements_minimal.txt .
RUN pip install --no-cache-dir -r requirements_minimal.txt

# Copy source code
COPY src/ ./src/

# Create generation script
COPY containers/sbom-generator/generate.py .

# Set environment variables
ENV GENERATOR_TYPE=sbom
ENV PYTHONPATH=/generator

CMD ["python3", "generate.py"]