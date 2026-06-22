# AgentGuard GitHub App

> **Automated AI agent security reviews on every PR.** Integrates AgentGuard into your GitHub workflow - scans diffs for OWASP ASI Top 10 vulnerabilities and posts review comments.

[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

## How It Works

1. Install the AgentGuard GitHub App on your repository
2. Every Pull Request triggers an automatic security scan
3. Findings appear as inline review comments on the affected lines
4. Critical/High findings can block PR merging (configurable)

## Deployment

### Self-hosted (Probot)

```bash
# Clone
git clone https://github.com/dockfixlabs/agentguard-app
cd agentguard-app

# Install
pip install -r requirements.txt
npm install

# Configure
cp .env.example .env
# Edit .env with your GitHub App credentials

# Run
npm start
```

### GitHub Actions (Alternative)

If you prefer not to run a server, use the GitHub Action instead:

```yaml
name: AgentGuard Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  agentguard:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install agentguard
      - run: agentguard . --format sarif > results.sarif
      - uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: results.sarif
      - name: Comment on PR
        run: |
          agentguard . --format json | python -c "
          import json, sys
          data = json.load(sys.stdin)
          if data['findings']:
              msg = '##  AgentGuard Security Review\n\n'
              msg += f'Found **{len(data[\"findings\"])}** security findings:\n\n'
              for f in data['findings']:
                  msg += f'- [{f[\"severity\"]}] {f[\"rule_name\"]} at {f[\"file\"]}:{f[\"line\"]}\n'
              print(msg)
          " >> comment.md
          gh pr comment ${{ github.event.pull_request.number }} --body-file comment.md
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Configuration

Create `.agentguard.yml` in your repo root:

```yaml
# Minimum severity to report
min_severity: MEDIUM

# Block PR merge on these severities
block_on:
  - CRITICAL

# Ignore specific rules
ignore_rules:
  - ASI08-CONTEXT-MANIPULATION  # Example: skip context checks

# Only scan specific directories
scan_paths:
  - src/
  - agents/
  - tools/
```

## Supported Checks

All 10 OWASP ASI Top 10 categories - see [AgentGuard](https://github.com/dockfixlabs/agentguard#detection-rules).

## License

MIT
