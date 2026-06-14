"""Small JSON serialization helpers for SDK return values."""

from __future__ import annotations

from typing import Any


def preview_to_dict(preview: Any) -> dict[str, Any]:
    """Serialize a capital_cli PreviewResult to the MCP tool's response shape."""
    return {
        "preview_id": preview.preview_id,
        "normalized_request": preview.normalized_request,
        "checks": [c.model_dump() for c in preview.checks],
        "all_checks_passed": preview.all_checks_passed,
        "estimated_entry": preview.estimated_entry,
        "estimated_risk_notes": preview.estimated_risk_notes,
        "expires_in_seconds": 120,
    }
