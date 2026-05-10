from datetime import datetime
import flet as ft
import httpx


def color(name: str, fallback):
    """Get a Flet color constant with a fallback for older Flet versions."""
    try:
        return getattr(ft.Colors, name)
    except Exception:
        return fallback


def http_error_detail(err: httpx.HTTPStatusError) -> str:
    """Return a readable error detail from an HTTPStatusError."""
    try:
        return err.response.json().get("detail", str(err))
    except Exception:
        return f"server error {err.response.status_code}"


def group_rewards_by_challenge(rewards):
    grouped = {}
    for reward in rewards:
        chall_id = reward.get("chall_id") if isinstance(reward, dict) else None
        if chall_id is None:
            continue
        grouped.setdefault(chall_id, []).append(reward)
    return grouped


def normalize_api_list(payload, keys=None):
    """Normalize API payloads into a list of dict records."""
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in (keys or ["items", "data", "results"]):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        for value in payload.values():
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def friendly_date(value: str) -> str:
    """Format YYYY-MM-DD to a shorter readable date."""
    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime("%d %b %Y")
    except Exception:
        return value or "unknown"


def loading_placeholder(label: str):
    return ft.Row(
        [
            ft.ProgressRing(width=14, height=14, stroke_width=2),
            ft.Text(label, size=12, color=ft.Colors.OUTLINE),
        ],
        spacing=8,
    )


def status_theme(status: str):
    muted_bg = color("SURFACE_VARIANT", color("SURFACE", None))
    muted_border = color("OUTLINE_VARIANT", ft.Colors.OUTLINE)
    muted_text = color("ON_SURFACE", ft.Colors.BLACK)
    if status == "completed":
        return {
            "badge": "completed",
            "text_color": color("ON_SECONDARY_CONTAINER", muted_text),
            "border_color": color("SECONDARY", muted_border),
            "bg_color": color("SECONDARY_CONTAINER", muted_bg),
        }
    if status == "failed":
        return {
            "badge": "failed",
            "text_color": color("ERROR", muted_text),
            "border_color": color("ERROR", muted_border),
            "bg_color": color("ERROR_CONTAINER", muted_bg),
        }
    return {
        "badge": "active",
        "text_color": muted_text,
        "border_color": muted_border,
        "bg_color": muted_bg,
    }
