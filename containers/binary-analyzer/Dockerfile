FROM ubuntu:22.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    binutils \
    file \
    libc-bin \
    python3 \
    python3-pip \
    curl \
    wget \
    unzip \
    openjdk-17-jre \
    git \
    && rm -rf /var/lib/apt/lists/*

# Note: radare2 can be installed later if needed for advanced analysis

# Set up working directory
WORKDIR /analyzer

# Copy requirements and install Python dependencies
COPY requirements_minimal.txt .
RUN pip3 install --no-cache-dir -r requirements_minimal.txt

# Copy source code
COPY src/ ./src/

# Create analysis script
COPY containers/binary-analyzer/analyze.py .

# Set environment variables
ENV ANALYZER_TYPE=binary
ENV PYTHONPATH=/analyzer

CMD ["python3", "analyze.py"]