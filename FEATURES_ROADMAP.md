# SBOM Platform Features Roadmap

## 🎯 Planned Features

### 1. 🔐 Secure Agent Framework
**Goal**: Implement a secure framework for remote SBOM analysis execution

#### Key Requirements:
- **Remote Execution**: Enable SBOM analysis on remote systems/agents
- **Security First**: Implement authentication, authorization, and encrypted communication
- **Agent Management**: Deploy, monitor, and manage remote agents
- **Sandboxing**: Ensure secure, isolated execution environments

#### Technical Considerations:
- mTLS for agent-to-orchestrator communication
- Agent authentication and registration workflow
- Resource limits and quotas per agent
- Audit logging for all remote operations

---

### 2. 🏗️ Container Architecture Cleanup
**Goal**: Streamline and optimize the container architecture

#### Completed Tasks: ✅
- Removed obsolete analyzer containers (cpp, java, binary, sbom-generator)
- Updated docker-compose.yml to single-container architecture
- Cleaned up unused container directories

#### Remaining Tasks:
- [ ] Optimize orchestrator container size
- [ ] Implement multi-stage Docker builds
- [ ] Create development vs production configurations
- [ ] Document container build process

---

### 3. 💾 Results Persistence Design
**Goal**: Design and implement a robust persistence layer for analysis results

#### Key Requirements:
- **Storage Options**: Support multiple backends (PostgreSQL, MongoDB, S3)
- **Data Retention**: Configurable retention policies
- **Query Interface**: Fast searching and filtering of historical results
- **Versioning**: Track SBOM versions and changes over time

#### Design Considerations:
- Database schema for efficient SBOM storage
- Indexing strategy for component searches
- Backup and recovery procedures
- Migration tools for schema updates

#### Proposed Architecture:
```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   FastAPI   │────▶│  Persistence │────▶│  Storage    │
│   Layer     │     │    Layer     │     │  Backend    │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │    Cache     │
                    │   (Redis)    │
                    └──────────────┘
```

---

## 📋 Implementation Priority

1. **High Priority**: Results Persistence (Foundation for other features)
2. **Medium Priority**: Container Architecture Optimization
3. **Future Priority**: Secure Agent Framework

## 🚀 Next Steps

1. Create detailed technical specifications for each feature
2. Set up feature branches for development
3. Define acceptance criteria and test plans
4. Establish development timeline and milestones

---

*Last Updated: January 2025*