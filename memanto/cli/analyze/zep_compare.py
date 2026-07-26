"""
Zep metrics and report stubs for the migrate command.

Zep does not have a comparison benchmark like Mem0/Letta/Supermemory,
so these are minimal stubs that produce a simple summary.
"""

from __future__ import annotations

from typing import Any


def compute_metrics(export: dict[str, Any]) -> dict[str, Any]:
    """Compute basic metrics from a Zep export."""
    threads = export.get("threads", []) or []
    total_messages = sum(len(t.get("messages", [])) for t in threads)
    total_summaries = sum(1 for t in threads if t.get("summary"))
    return {
        "thread_count": len(threads),
        "message_count": total_messages,
        "summary_count": total_summaries,
        "provider": "zep",
    }


def build_llm_prompt(metrics: dict[str, Any]) -> str:
    """Build a minimal prompt for the narrative."""
    return (
        f"Zep export summary: {metrics.get('thread_count', 0)} threads, "
        f"{metrics.get('message_count', 0)} messages, "
        f"{metrics.get('summary_count', 0)} summaries."
    )


def build_report_markdown(
    metrics: dict[str, Any],
    narrative: str,
    export_path: str,
    llm_model: str,
    llm_method: str,
    exported_at: str | None,
) -> str:
    """Build a simple markdown report."""
    lines = [
        "# Zep → Memanto Migration Report",
        "",
        f"**Threads exported:** {metrics.get('thread_count', 0)}",
        f"**Messages exported:** {metrics.get('message_count', 0)}",
        f"**Summaries exported:** {metrics.get('summary_count', 0)}",
        f"**Export file:** `{export_path}`",
        f"**Exported at:** {exported_at or 'N/A'}",
    ]
    if narrative:
        lines.extend(["", "## Narrative", "", narrative])
    return "\n".join(lines)