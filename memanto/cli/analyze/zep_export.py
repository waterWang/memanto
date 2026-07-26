"""
Export all Zep (Cloud) thread data to JSON.

Used by ``memanto migrate zep``. Pure ``httpx`` — no Zep SDK dependency,
so users don't have to install ``zep_cloud`` and we don't break when the SDK
ships a new version.

Endpoints (Zep Cloud REST API v2):
    GET  /threads?page_number=&page_size=       list all threads
    GET  /threads/{thread_id}/messages?limit=    get messages for a thread
    GET  /threads/{thread_id}/summary            get thread summary

Auth: ``Authorization: Bearer <api_key>`` (Zep Cloud API key).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

import httpx

API_BASE = "https://api.getzep.com/api/v2"
DEFAULT_PAGE_SIZE = 50
REQUEST_TIMEOUT_S = 60.0


def _client(api_key: str) -> httpx.Client:
    return httpx.Client(
        base_url=API_BASE,
        timeout=REQUEST_TIMEOUT_S,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )


def _get_json(
    client: httpx.Client, path: str, params: dict[str, Any] | None = None
) -> Any:
    resp = client.get(path, params=params or {})
    if resp.status_code >= 400:
        raise RuntimeError(f"GET {path} -> {resp.status_code}: {resp.text[:500]}")
    return resp.json() if resp.content else {}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def fetch_threads(client: httpx.Client) -> list[dict[str, Any]]:
    """Fetch all threads with pagination."""
    all_threads: list[dict[str, Any]] = []
    page = 1

    while True:
        data = _get_json(
            client,
            "threads",
            params={
                "page_number": page,
                "page_size": DEFAULT_PAGE_SIZE,
                "order_by": "created_at",
                "asc": "true",
            },
        )
        threads = data.get("threads") or []
        if not threads:
            break
        all_threads.extend(threads)
        total_count = data.get("total_count", 0)
        if total_count and len(all_threads) >= total_count:
            break
        page += 1

    return all_threads


def fetch_messages(
    client: httpx.Client, thread_id: str, limit: int = 200
) -> list[dict[str, Any]]:
    """Fetch all messages for a thread."""
    data = _get_json(
        client,
        f"threads/{thread_id}/messages",
        params={"limit": limit},
    )
    return data.get("messages") or []


def fetch_summary(
    client: httpx.Client, thread_id: str
) -> dict[str, Any] | None:
    """Fetch the summary for a thread, if one exists."""
    try:
        data = _get_json(client, f"threads/{thread_id}/summary")
        if data and data.get("summary"):
            return data
    except RuntimeError:
        pass
    return None


def run_zep_export(
    api_key: str,
    run_dir: Path,
    on_progress: Any = None,
) -> tuple[Path, dict[str, Any]]:
    """Run the full Zep export and return (export_path, export_data)."""
    cli = _client(api_key)

    if on_progress:
        on_progress("Fetching Zep threads...")

    threads = fetch_threads(cli)
    if on_progress:
        on_progress(f"Found {len(threads)} threads — fetching messages...")

    exported_memories: list[dict[str, Any]] = []

    for idx, thread in enumerate(threads):
        thread_id = thread.get("thread_id") or thread.get("uuid") or ""
        if not thread_id:
            continue

        if on_progress and idx % 10 == 0:
            on_progress(f"  [{idx + 1}/{len(threads)}] Processing thread {thread_id[:12]}...")

        messages = fetch_messages(cli, thread_id)
        summary = fetch_summary(cli, thread_id)

        user_id = thread.get("user_id") or thread.get("user_uuid") or ""

        exported_memories.append({
            "thread_id": thread_id,
            "user_id": user_id,
            "created_at": thread.get("created_at"),
            "project_uuid": thread.get("project_uuid"),
            "messages": [
                {
                    "uuid": msg.get("uuid"),
                    "role": str(msg.get("role", "user")),
                    "content": msg.get("content", ""),
                    "created_at": msg.get("created_at"),
                    "metadata": msg.get("metadata"),
                    "name": msg.get("name"),
                }
                for msg in (messages or [])
                if msg.get("content")
            ],
            "summary": summary.get("summary") if summary else None,
            "summary_created_at": summary.get("created_at") if summary else None,
        })

    export = {
        "exported_at": _now_iso(),
        "provider": "zep",
        "thread_count": len(threads),
        "memory_count": sum(
            len(m.get("messages", [])) for m in exported_memories
        ),
        "threads": exported_memories,
    }

    run_dir.mkdir(parents=True, exist_ok=True)
    export_path = run_dir / "zep_export.json"
    export_path.write_text(
        json.dumps(export, indent=2, default=str), encoding="utf-8"
    )

    if on_progress:
        on_progress(
            f"Zep export complete: {export['thread_count']} threads, "
            f"{export['memory_count']} messages"
        )

    return export_path, export