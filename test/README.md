# Go Application Service - Red Hat Docker Image

This project contains a Go application that runs directly in a Red Hat-based Docker container.

## Application Features

- Logs "Hello from GO !!!" with timestamp to `/tmp/app.log` every 30 seconds
- Automatically rotates log file when it exceeds 1MB by deleting and recreating it
- Runs as a long-running process (no systemd needed)
- Uses a non-root user for security

## Files

- `main.go` - The Go application source code
- `go.mod` - Go module file
- `Dockerfile` - Red Hat UBI-based Docker image
- `docker-compose.yml` - Docker Compose configuration

## Building and Running

### Option 1: Using Docker Compose (Recommended)

```bash
# Build and run the container
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down
```

### Option 2: Using Docker directly

```bash
# Build the image
docker build -t goapp-redhat .

# Run the container
docker run -d --name goapp-service goapp-redhat

# View application logs (stdout/stderr)
docker logs -f goapp-service

# View the log file
docker exec goapp-service cat /tmp/app.log
```

## Monitoring

### View application logs (stdout/stderr)
```bash
docker logs -f goapp-service
```

### View the application log file
```bash
docker exec goapp-service cat /tmp/app.log
```

### Monitor log file size
```bash
docker exec goapp-service ls -lh /tmp/app.log
```

### Check if container is running
```bash
docker ps | grep goapp-service
```

## Notes

- The application runs directly as the main process (PID 1)
- The application runs as the `goapp` user for security
- Log rotation happens automatically when the file exceeds 1MB
- Docker will automatically restart the container if it crashes (with restart policy)
- Uses Red Hat Universal Base Image (UBI) 9 for enterprise compatibility
- No systemd needed - simpler and more container-friendly approach
