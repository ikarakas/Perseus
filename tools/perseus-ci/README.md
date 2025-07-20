# Perseus CI/CD Integration

Platform-agnostic CI/CD integration for automated SBOM generation and vulnerability scanning.

## Overview

The Perseus CI tool enables seamless integration of SBOM scanning into any CI/CD pipeline. It provides:

- 🚀 **Simple synchronous scanning** - Block builds with vulnerabilities
- 🔍 **Auto-detection** of CI/CD platforms (Jenkins, GitLab, GitHub Actions, etc.)
- 📊 **Configurable thresholds** - Fail on critical, high, medium, or low vulnerabilities
- 📄 **Multiple output formats** - JSON reports for further processing
- 🏗️ **Zero dependencies** - Single Python script, works everywhere

## Quick Start

### 1. Basic Usage

```bash
# Simple scan (current directory)
python3 perseus-ci.py scan --fail-on critical

# Scan specific project
python3 perseus-ci.py scan --project-path ./my-app --fail-on critical,high

# Save results to file
python3 perseus-ci.py scan --output scan-results.json

# Health check
python3 perseus-ci.py health
```

### 2. Vulnerability Scanning Features

The Perseus CI tool provides comprehensive vulnerability scanning with the following capabilities:

#### Automatic Project Detection
- Detects Java Maven projects (`pom.xml`)
- Identifies Python projects (`requirements.txt`, `setup.py`)
- Recognizes Node.js projects (`package.json`)
- Handles Go modules (`go.mod`)
- Supports Docker projects (`Dockerfile`)

#### Vulnerability Thresholds
```bash
# Fail build on critical vulnerabilities only
python3 perseus-ci.py scan --fail-on critical

# Fail on critical and high severity
python3 perseus-ci.py scan --fail-on critical,high

# Fail on medium and above
python3 perseus-ci.py scan --fail-on critical,high,medium

# Fail on any vulnerabilities (strictest)
python3 perseus-ci.py scan --fail-on critical,high,medium,low
```

#### Output Options
```bash
# Console output only (default)
python3 perseus-ci.py scan

# Save detailed JSON report
python3 perseus-ci.py scan --output vulnerabilities.json

# Save with custom filename
python3 perseus-ci.py scan --output "${BUILD_NUMBER}-security-report.json"
```

#### Scan Results Format
The tool outputs vulnerability counts and details:
```
📊 Scan Results:
   Components found: 25
   Vulnerabilities:
     🔴 Critical: 2
     🟠 High: 5
     🟡 Medium: 8
     🟢 Low: 3

💾 Report saved to: vulnerabilities.json
```

#### JSON Report Structure
```json
{
  "analysis_id": "abc123-def456",
  "status": "completed",
  "components": [
    {
      "name": "log4j-core",
      "version": "2.14.0",
      "purl": "pkg:maven/org.apache.logging.log4j/log4j-core@2.14.0",
      "vulnerability_count": 4,
      "critical_vulnerabilities": 2
    }
  ],
  "vulnerability_summary": {
    "critical": 2,
    "high": 5,
    "medium": 8,
    "low": 3,
    "total": 18
  },
  "scan_metadata": {
    "scan_date": "2025-07-20T12:55:20Z",
    "scan_duration_seconds": 45.2,
    "components_scanned": 25
  }
}
```

### 2. Environment Variables

```bash
export PERSEUS_API_URL=http://perseus.example.com:8000
export PERSEUS_API_KEY=your-api-key
export PERSEUS_PROJECT_ID=my-project
export PERSEUS_TIMEOUT=600
```

### 3. CI/CD Platform Examples

#### Jenkins
```groovy
pipeline {
    agent any
    environment {
        PERSEUS_API_URL = 'http://perseus.internal:8000'
        PERSEUS_API_KEY = credentials('perseus-api-key')
    }
    stages {
        stage('Security Scan') {
            steps {
                script {
                    sh '''
                        python3 tools/perseus-ci/perseus-ci.py scan \
                            --fail-on critical,high \
                            --output "security-report-${BUILD_NUMBER}.json"
                    '''
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: 'security-report-*.json', fingerprint: true
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: false,
                        keepAll: true,
                        reportDir: '.',
                        reportFiles: 'security-report-*.json',
                        reportName: 'Security Scan Report'
                    ])
                }
                failure {
                    emailext (
                        subject: "Security Scan Failed: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                        body: "Critical or high severity vulnerabilities found. Check report for details.",
                        to: "${env.CHANGE_AUTHOR_EMAIL}"
                    )
                }
            }
        }
    }
}
```

#### GitLab CI
```yaml
variables:
  PERSEUS_API_URL: "https://perseus.gitlab.com:8000"

perseus-security-scan:
  stage: security
  image: python:3.11-slim
  before_script:
    - apt-get update && apt-get install -y curl
  script:
    - python3 tools/perseus-ci/perseus-ci.py scan --fail-on critical,high --output security-report.json
  artifacts:
    reports:
      dependency_scanning: security-report.json
    paths:
      - security-report.json
    expire_in: 30 days
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
    - if: $CI_MERGE_REQUEST_IID
  allow_failure: false

# Optional: Security gate for production
security-gate:
  stage: deploy
  script:
    - python3 tools/perseus-ci/perseus-ci.py scan --fail-on critical --output production-security-check.json
  only:
    - tags
    - main
  when: manual
```

#### GitHub Actions
```yaml
name: Security Scan

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    
    env:
      PERSEUS_API_URL: ${{ secrets.PERSEUS_API_URL }}
      PERSEUS_API_KEY: ${{ secrets.PERSEUS_API_KEY }}
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Perseus Security Scan
      run: |
        python3 tools/perseus-ci/perseus-ci.py scan \
          --fail-on critical,high \
          --output security-report-${{ github.run_number }}.json
    
    - name: Upload Security Report
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: security-report
        path: security-report-*.json
        retention-days: 30
    
    - name: Security Gate
      if: github.ref == 'refs/heads/main'
      run: |
        python3 tools/perseus-ci/perseus-ci.py scan \
          --fail-on critical \
          --output production-gate-check.json

# Optional: Schedule regular security scans
  scheduled-scan:
    runs-on: ubuntu-latest
    if: github.event_name == 'schedule'
    
    steps:
    - uses: actions/checkout@v3
    - name: Weekly Security Scan
      run: |
        python3 tools/perseus-ci/perseus-ci.py scan \
          --fail-on medium,high,critical \
          --output weekly-security-scan.json
```

#### Azure DevOps
```yaml
trigger:
- main
- develop

pool:
  vmImage: 'ubuntu-latest'

variables:
  PERSEUS_API_URL: $(PerseusApiUrl)
  PERSEUS_API_KEY: $(PerseusApiKey)

stages:
- stage: SecurityScan
  displayName: 'Security Vulnerability Scan'
  jobs:
  - job: VulnerabilityScan
    displayName: 'Run Perseus Security Scan'
    steps:
    - task: UsePythonVersion@0
      inputs:
        versionSpec: '3.11'
    
    - script: |
        python3 tools/perseus-ci/perseus-ci.py scan \
          --fail-on critical,high \
          --output security-report-$(Build.BuildNumber).json
      displayName: 'Perseus Vulnerability Scan'
    
    - task: PublishBuildArtifacts@1
      condition: always()
      inputs:
        pathToPublish: 'security-report-$(Build.BuildNumber).json'
        artifactName: 'SecurityReport'
        publishLocation: 'Container'
    
    - task: PublishTestResults@2
      condition: always()
      inputs:
        testResultsFormat: 'JUnit'
        testResultsFiles: 'security-report-*.json'
        testRunTitle: 'Security Vulnerability Scan'

- stage: ProductionGate
  displayName: 'Production Security Gate'
  condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
  jobs:
  - deployment: SecurityGate
    displayName: 'Security Gate Check'
    environment: 'production'
    strategy:
      runOnce:
        deploy:
          steps:
          - script: |
              python3 tools/perseus-ci/perseus-ci.py scan \
                --fail-on critical \
                --output production-gate-$(Build.BuildNumber).json
            displayName: 'Production Security Gate'
```

#### CircleCI
```yaml
version: 2.1

orbs:
  python: circleci/python@2.0.3

jobs:
  security-scan:
    docker:
      - image: cimg/python:3.11
    environment:
      PERSEUS_API_URL: https://perseus.circle.com:8000
    steps:
      - checkout
      - python/install-packages:
          pkg-manager: pip
      - run:
          name: Perseus Security Scan
          command: |
            python3 tools/perseus-ci/perseus-ci.py scan \
              --fail-on critical,high \
              --output security-report-${CIRCLE_BUILD_NUM}.json
      - store_artifacts:
          path: security-report-*.json
          destination: security-reports
      - store_test_results:
          path: security-report-*.json

workflows:
  version: 2
  build-and-scan:
    jobs:
      - security-scan:
          filters:
            branches:
              only:
                - main
                - develop
  
  nightly-security-scan:
    triggers:
      - schedule:
          cron: "0 2 * * *"
          filters:
            branches:
              only:
                - main
    jobs:
      - security-scan
```

## Pattern 1: Synchronous Scanning (Simple)

This implementation provides the simplest integration pattern:

1. **Submit scan request** - CLI sends project info to Perseus API
2. **Wait for completion** - Blocks until scan finishes
3. **Check thresholds** - Fails build if vulnerabilities exceed limits
4. **Generate report** - Outputs JSON report with results

### How It Works

```
CI/CD Pipeline          Perseus CLI              Perseus API
     |                       |                        |
     |------ Run CLI ------->|                        |
     |                       |---- Register Build --->|
     |                       |<---- Build ID ---------|
     |                       |                        |
     |                       |---- Start Scan ------->|
     |                       |<--- Analysis ID -------|
     |                       |                        |
     |                       |---- Poll Status ------>|
     |                       |<--- In Progress -------|
     |                       |         ...            |
     |                       |---- Poll Status ------>|
     |                       |<--- Completed ---------|
     |                       |                        |
     |                       |---- Get Results ------>|
     |                       |<--- Full Results ------|
     |                       |                        |
     |<-- Exit Code (0/1) ---|                        |
     |                       |                        |
```

## API Endpoints

The CI/CD integration adds these endpoints to Perseus:

- `POST /api/v1/cicd/builds` - Register a new build
- `POST /api/v1/cicd/builds/{id}/scan` - Start scanning
- `GET /api/v1/cicd/builds/{id}/status` - Check scan status
- `GET /api/v1/cicd/builds/{id}/results` - Get scan results
- `GET /api/v1/cicd/builds/{id}/artifacts` - Download generated SBOMs

## Testing

Run the test script to verify your integration:

```bash
cd examples/cicd
./test-cicd-integration.sh
```

## Advanced Features (Coming Soon)

- **Pattern 2: Asynchronous scanning** with webhooks
- **Pattern 3: Policy-based gates** for compliance
- **Incremental scanning** for faster builds
- **Dependency caching** to reduce scan time
- **Custom policies** as code

## Troubleshooting

### API Connection Issues
```bash
# Check API health
perseus-ci health

# Verify API URL
echo $PERSEUS_API_URL
```

### Authentication Errors
```bash
# Ensure API key is set
export PERSEUS_API_KEY=your-key-here
```

### Timeout Issues
```bash
# Increase timeout (default: 300 seconds)
export PERSEUS_TIMEOUT=600
```

## Security Considerations

1. **API Keys** - Store in CI/CD secrets, never in code
2. **Network** - Use HTTPS in production
3. **Permissions** - Use read-only keys for CI/CD
4. **Audit** - All scans are logged with CI context

## Support

For issues or questions:
- Email: ilkermurat.karakas@naew.nato.int
- Documentation: [Perseus SBOM Platform](https://perseus.example.com/docs)