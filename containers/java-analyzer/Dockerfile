FROM openjdk:17-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    maven \
    gradle \
    python3 \
    python3-pip \
    curl \
    wget \
    unzip \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install OWASP Dependency Check
RUN wget -O /tmp/dependency-check.zip \
    https://github.com/jeremylong/DependencyCheck/releases/download/v8.4.0/dependency-check-8.4.0-release.zip \
    && unzip /tmp/dependency-check.zip -d /opt/ \
    && ln -s /opt/dependency-check/bin/dependency-check.sh /usr/local/bin/dependency-check \
    && rm /tmp/dependency-check.zip

# Set up working directory
WORKDIR /analyzer

# Copy requirements and install Python dependencies
COPY requirements_minimal.txt .
RUN pip3 install --no-cache-dir -r requirements_minimal.txt

# Copy source code
COPY src/ ./src/

# Create analysis script
COPY containers/java-analyzer/analyze.py .

# Set environment variables
ENV ANALYZER_TYPE=java
ENV PYTHONPATH=/analyzer
ENV JAVA_HOME=/usr/local/openjdk-17

CMD ["python3", "analyze.py"]