# Debug Tools

This directory contains debugging scripts and files created during development and troubleshooting.

## Files

### Testing Scripts
- **`test_path_normalization.py`** - Test script for path normalization functionality
  - Tests trailing slash handling in binary analysis
  - Verifies both `/path/` and `/path` work correctly

- **`test_osv_debug.py`** - Debug script for OSV vulnerability scanner
  - Tests OSV API connectivity and response parsing
  - Used to debug vulnerability scanning issues

### Debug Artifacts  
- **`vulnerability_demo.html`** - Demo page showing vulnerability enhancements
  - Documents the enhanced vulnerability details feature
  - Shows before/after of vulnerability detection improvements

- **`api.log`** - API debug log file
  - Contains debugging output from API testing
  - Includes error traces and request/response logs

## Usage

These scripts can be run for debugging purposes:

```bash
# Test path normalization
python tools/debug/test_path_normalization.py

# Test OSV scanner (requires running service)
python tools/debug/test_osv_debug.py
```

## Note

These are temporary debugging files created during issue resolution. They can be safely removed if no longer needed for debugging purposes.