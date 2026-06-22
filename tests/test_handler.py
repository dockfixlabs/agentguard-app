"""Tests for AgentGuard App handler."""
import pytest
from app.handler import format_pr_comment, should_block_merge


def test_clean_result_comment():
    result = {"findings": []}
    comment = format_pr_comment(result)
    assert "No vulnerabilities" in comment


def test_findings_comment():
    result = {
        "findings": [
            {
                "severity": "CRITICAL",
                "rule_name": "Prompt Injection",
                "file": "agent.py",
                "line": 42,
                "description": "Bad input in prompt",
                "recommendation": "Sanitize input",
            }
        ]
    }
    comment = format_pr_comment(result)
    assert "1" in comment
    assert "CRITICAL" in comment
    assert "Prompt Injection" in comment
    assert "agent.py" in comment


def test_block_merge_on_critical():
    result = {"findings": [{"severity": "CRITICAL"}]}
    assert should_block_merge(result) == True


def test_no_block_on_medium():
    result = {"findings": [{"severity": "MEDIUM"}]}
    assert should_block_merge(result) == False


def test_block_config_custom():
    result = {"findings": [{"severity": "MEDIUM"}]}
    assert should_block_merge(result, {"block_on": ["MEDIUM"]}) == True


def test_no_findings_no_block():
    result = {"findings": []}
    assert should_block_merge(result) == False