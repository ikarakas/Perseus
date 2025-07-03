FROM ubuntu:22.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    cppcheck \
    libclang-dev \
    bear \
    binutils \
    libc-bin \
    python3 \
    python3-pip \
    curl \
    git \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install include-what-you-use
RUN apt-get update && apt-get install -y \
    iwyu \
    && rm -rf /var/lib/apt/lists/*

# Install Conan package manager
RUN pip3 install conan

# Set up working directory
WORKDIR /analyzer

# Copy requirements and install Python dependencies
COPY requirements_minimal.txt .
RUN pip3 install --no-cache-dir -r requirements_minimal.txt

# Copy source code
COPY src/ ./src/

# Create analysis script
COPY containers/cpp-analyzer/analyze.py .

# Set environment variables
ENV ANALYZER_TYPE=cpp
ENV PYTHONPATH=/analyzer

CMD ["python3", "analyze.py"]