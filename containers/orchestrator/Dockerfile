FROM alpine:3.19

# Install system dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    docker-cli \
    curl \
    git \
    wget \
    tar \
    gcc \
    python3-dev \
    musl-dev \
    linux-headers

# Install Syft
RUN curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin

WORKDIR /app

COPY requirements_minimal.txt .
RUN pip3 install --break-system-packages --no-cache-dir -r requirements_minimal.txt

COPY src/ ./src/
COPY containers/orchestrator/app.py .
COPY README.md .

EXPOSE 8080

CMD ["python3", "app.py"]