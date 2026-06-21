"""AgentGuard GitHub App entry point."""

from __future__ import annotations
import os
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

from app.handler import scan_pr_diff, format_pr_comment, should_block_merge

app = FastAPI(title="AgentGuard GitHub App", version="0.1.0")


@app.post("/webhook")
async def webhook(request: Request) -> JSONResponse:
    """Handle GitHub webhook events."""
    event = request.headers.get("X-GitHub-Event", "")
    payload = await request.json()

    if event == "pull_request" and payload.get("action") in ("opened", "synchronize"):
        return await handle_pr_event(payload)

    return JSONResponse({"status": "ignored", "event": event})


async def handle_pr_event(payload: dict) -> JSONResponse:
    """Handle pull_request events — scan and comment."""
    pr = payload.get("pull_request", {})
    repo = payload.get("repository", {})

    pr_number = pr.get("number")
    diff_url = pr.get("diff_url")
    repo_full_name = repo.get("full_name", "")
    repo_clone_url = repo.get("clone_url", "")

    if not pr_number or not diff_url:
        raise HTTPException(status_code=400, detail="Missing PR data")

    # Clone repo to temp dir and scan
    import tempfile, subprocess
    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.run(
            ["git", "clone", "--depth", "1", repo_clone_url, tmpdir],
            capture_output=True,
            timeout=60,
        )

        scan_result = await scan_pr_diff(diff_url, tmpdir)

    # Post comment
    comment = format_pr_comment(scan_result)
    token = os.environ.get("GITHUB_TOKEN", "")

    if token:
        api_url = f"https://api.github.com/repos/{repo_full_name}/issues/{pr_number}/comments"
        async with httpx.AsyncClient() as client:
            await client.post(
                api_url,
                json={"body": comment},
                headers={
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github.v3+json",
                },
            )

    # Check if should block
    blocked = should_block_merge(scan_result)

    return JSONResponse({
        "status": "scanned",
        "pr": pr_number,
        "findings": len(scan_result.get("findings", [])),
        "blocked": blocked,
    })


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "agentguard-app", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
