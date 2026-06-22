# Changelog

All notable changes to AgentGuard App will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-06-21

### Added
- FastAPI webhook handler for pull_request events
- Scans PRs with AgentGuard, posts review comments
- Configurable block-on severity
- GitHub Actions alternative workflow included
- .agentguard.yml config file support
- 6 test cases