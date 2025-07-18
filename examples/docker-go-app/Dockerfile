# Use Red Hat Universal Base Image (UBI) 9
FROM registry.access.redhat.com/ubi9/ubi:latest

# Install Go
RUN dnf update -y && \
    dnf install -y golang && \
    dnf clean all

# Create a non-root user for the application
RUN groupadd -r goapp && useradd -r -g goapp goapp

# Set working directory
WORKDIR /app

# Copy Go source files
COPY go.mod ./
COPY main.go ./

# Build the Go application
RUN go mod tidy && \
    go build -o goapp main.go

# Create the log directory and set permissions
RUN mkdir -p /var/log && \
    chown goapp:goapp /var/log

# Create a startup script that ensures proper permissions
RUN cat > /app/start.sh << 'EOF'
#!/bin/bash
# Ensure log directory has proper permissions
sudo chown goapp:goapp /var/log
# Start the application
exec ./goapp
EOF

RUN chmod +x /app/start.sh

# Install sudo for the startup script
RUN dnf install -y sudo && \
    echo "goapp ALL=(ALL) NOPASSWD: /bin/chown" >> /etc/sudoers

# Switch to non-root user
USER goapp

# Expose any necessary ports (if needed in the future)
# EXPOSE 8080

# Run the startup script
CMD ["/app/start.sh"]
