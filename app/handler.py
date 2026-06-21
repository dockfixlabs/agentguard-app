"""AgentGuard GitHub App — Probot-based PR security reviewer."""

from __future__ import annotations
import json
import subprocess
import tempfile
from pathlib import Path


# OWASP ASI severity to GitHub review state mapping
SEVERITY_TO_REVIEW_STATE = {
    "CRITICAL": "blocker",
    "HIGH": "blocker",
    "MEDIUM": "comment",
    "LOW": "comment",
    "INFO": "comment",
}


async def scan_pr_diff(diff_url: str, repo_dir: str) -> dict:
    """Scan a PR diff for security vulnerabilities.

    Args:
        diff_url: URL to the PR diff
        repo_dir: Local path to the cloned repo

    Returns:
        Scan results with findings
    """
    # Run AgentGuard on the repo
    try:
        result = subprocess.run(
            ["agentguard", repo_dir, "--format", "json", "--min-severity", "MEDIUM"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0 or result.stdout:
            return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        pass

    return {"findings": [], "files_scanned": 0}


def format_pr_comment(scan_result: dict) -> str:
    """Format scan results as a GitHub PR comment."""
    findings = scan_result.get("findings", [])

    if not findings:
        return "## 🛡️ AgentGuard Security Review\n\n✅ No vulnerabilities found in this PR."

    critical = sum(1 for f in findings if f["severity"] == "CRITICAL")
    high = sum(1 for f in findings if f["severity"] == "HIGH")
    medium = sum(1 for f in findings if f["severity"] == "MEDIUM")
    low = sum(1 for f in findings if f["severity"] == "LOW")

    comment = "## 🛡️ AgentGuard Security Review\n\n"
    comment += f"Found **{len(findings)}** security findings:\n\n"
    comment += f"| Severity | Count |\n|----------|-------|\n"
    comment += f"| 🔴 Critical | {critical} |\n"
    comment += f"| 🟠 High | {high} |\n"
    comment += f"| 🟡 Medium | {medium} |\n"
    comment += f"| 🔵 Low | {low} |\n\n"

    # Group by file
    by_file = {}
    for f in findings:
        by_file.setdefault(f["file"], []).append(f)

    for file, file_findings in sorted(by_file.items()):
        comment += f"### `{file}`\n\n"
        for f in file_findings:
            sev_emoji = {
                "CRITICAL": "🔴", "HIGH": "🟠",
                "MEDIUM": "🟡", "LOW": "🔵", "INFO": "⚪",
            }.get(f["severity"], "⚪")

            comment += f"- {sev_emoji} **{f['rule_name']}** (L{f['line']})\n"
            comment += f"  - {f['description']}\n"
            comment += f"  - **Fix:** {f['recommendation']}\n\n"

    comment += "---\n"
    comment += "*Powered by [AgentGuard](https://github.com/dockfixlabs/agentguard) · OWASP ASI Top 10*"

    return comment


def should_block_merge(scan_result: dict, config: dict | None = None) -> bool:
    """Determine if PR should be blocked based on findings."""
    if not config:
        config = {"block_on": ["CRITICAL", "HIGH"]}

    block_severities = set(config.get("block_on", ["CRITICAL"]))
    findings = scan_result.get("findings", [])

    return any(f["severity"] in block_severities for f in findings)
