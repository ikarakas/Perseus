# Tool Path Detection

This document explains how the SBOM platform detects and configures paths for external tools (Syft and Grype) in different environments.

## Problem

The SBOM platform runs in two different environments:
- **Production**: Linux container with tools installed at `/usr/local/bin/`
- **Development**: macOS/Linux with tools installed via Homebrew or other package managers

## Solution

The platform now uses intelligent path detection that works in both environments:

### 1. Environment Detection

The system detects if it's running in a container by checking:
- Existence of `/.dockerenv` file
- `CONTAINER_ENV` environment variable

### 2. Path Resolution Order

Tools are located using the following priority:

1. **Environment Variables** (highest priority)
   - `SYFT_PATH` - explicit path to Syft binary
   - `GRYPE_PATH` - explicit path to Grype binary

2. **Which Command**
   - Uses `which syft` or `which grype` to find tools in PATH

3. **Common Locations** (environment-specific)
   - **Container paths**: `/usr/local/bin/`, `/usr/bin/`, `/opt/syft/`
   - **Development paths**: `/opt/homebrew/bin/`, `/usr/local/bin/`, `/usr/bin/`

4. **PATH Environment Search**
   - Searches all directories in PATH environment variable

### 3. Docker Configuration

The Dockerfile sets environment variables to ensure consistent behavior in containers:

```dockerfile
ENV SYFT_PATH=/usr/local/bin/syft
ENV GRYPE_PATH=/usr/local/bin/grype
ENV CONTAINER_ENV=true
```

### 4. Error Handling

The improved error handling now:
- Captures both stdout and stderr from subprocess calls
- Provides specific error messages for common Docker issues
- Logs detailed debugging information
- Handles FileNotFoundError when binaries don't exist

## Testing

To test tool detection in your environment:

```bash
# Run the shell script test
./tests/test_tool_paths.sh

# Or use environment variables to override
SYFT_PATH=/custom/path/to/syft python src/api/main.py
```

## Troubleshooting

If tools are not detected:

1. **Check installation**: Ensure Syft and Grype are installed
2. **Check PATH**: Make sure tool directories are in your PATH
3. **Use environment variables**: Set `SYFT_PATH` and `GRYPE_PATH` explicitly
4. **Check permissions**: Ensure tools are executable (`chmod +x`)
5. **Check logs**: Look for "Found syft at:" messages in application logs