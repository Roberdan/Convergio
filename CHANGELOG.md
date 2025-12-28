# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0] - 2025-12-28

### Added
- **Web App Release Manager Agent** - BRUTAL mode enforcement for pre-release quality checks
- **Comprehensive cleanup**: 542 files cleaned up and reorganized
- **SvelteKit 2 + Svelte 5** frontend migration
- **Version consistency enforcement** across all package files
- **Automated security audits** with npm audit integration
- **Code quality gates** - zero tolerance for TODO/FIXME/console.log in releases

### Changed
- **BREAKING**: Frontend framework migrated from SvelteKit 1 to SvelteKit 2 with Svelte 5
- **BREAKING**: Major codebase restructuring and cleanup
- Version management now enforced across VERSION, package.json, and all submodules

### Fixed
- Version inconsistencies across monorepo packages
- Frontend build configuration for production deployments

### Removed
- Legacy code and unused dependencies from major cleanup

## [2.1.0] - 2025-12-XX

### Added
- **Ollama-First AI Provider System** with local model support
- **Strict Mode** for blocking all cloud API calls (ollama_only mode)
- **Per-Agent Provider Override** configuration
- **Per-Feature Provider Override** (chat, code review, embeddings)
- **Real-time Cost Tracking** with $0 cost for Ollama
- **Azure Cost Management API** integration
- **GPU Detection** for optimal model selection

### Changed
- AI provider architecture to support hybrid local/cloud deployments
- Cost tracking system with provider-specific metrics

## [2.0.0] - 2025-12-XX

### Added
- **Microsoft Agent Framework 1.0** migration from AutoGen
- **AgentFrameworkOrchestrator** with native streaming support
- **Dual-Framework Adapters** for backward compatibility
- **Feature Flags** system with `FrameworkFeatureFlags`
- **431+ passing tests** including 276 new framework tests
- **Enhanced Memory System** with `AgentFrameworkMemory`
- **Production Docker support**

### Changed
- **BREAKING**: Framework migration from Microsoft AutoGen to Agent Framework 1.0
- **BREAKING**: Orchestration patterns modernized with streaming
- Memory system enhanced with dedicated context management
- Tools architecture unified into Tools Registry

### Removed
- Deprecated AutoGen-specific implementations (kept in compatibility layer)

## [1.0.0] - 2025-XX-XX

### Added
- Initial release of Convergio platform
- AI-first orchestration with specialized agent crew
- FastAPI backend with Python 3.11+
- SvelteKit frontend (v1)
- Multi-provider AI support (OpenAI, Anthropic, Azure)

[3.0.0]: https://github.com/Roberdan/Convergio/releases/tag/v3.0.0
[2.1.0]: https://github.com/Roberdan/Convergio/releases/tag/v2.1.0
[2.0.0]: https://github.com/Roberdan/Convergio/releases/tag/v2.0.0
[1.0.0]: https://github.com/Roberdan/Convergio/releases/tag/v1.0.0
