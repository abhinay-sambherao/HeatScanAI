"""Check every MANUFACTURER_SITES base/search URL plus robots.txt.

Outputs a markdown table suitable for docs/MANUFACTURER_URL_CHECKLIST.md.

Usage (run from backend/):
    python -m scripts.check_manufacturer_urls
"""

from __future__ import annotations

import argparse
import ast
import asyncio
import json
from pathlib import Path
from urllib.parse import urlsplit

import httpx

BACKEND = Path(__file__).resolve().parents[1] / "backend"
SCAPER = BACKEND / "app" / "services" / "manufacturer_scraper.py"


def _load_sites() -> dict:
    """Extract MANUFACTURER_SITES without importing the scraper module."""
    tree = ast.parse(SCAPER.read_text())
    for node in ast.walk(tree):
        target = None
        if isinstance(node, ast.Assign):
            target = node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            target = node.value
        if target is None:
            continue
        for t in getattr(node, "targets", [node.target if isinstance(node, ast.AnnAssign) else None]) or []:
            if isinstance(t, ast.Name) and t.id == "MANUFACTURER_SITES":
                return ast.literal_eval(target)
    raise RuntimeError("MANUFACTURER_SITES not found")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
}

MODEL = "Vitodens"


def _status_emoji(code: int | None) -> tuple[str, str]:
    if code is None:
        return "❌", "unreachable"
    if code == 403:
        return "🛡️", f"{code} (bot-blocked)"
    if code == 429:
        return "⚠️", f"{code} (rate-limited)"
    if 200 <= code < 300:
        return "✅", str(code)
    if code == 301 or code == 302 or code == 303 or code == 307 or code == 308:
        return "🔀", f"{code} (redirect)"
    return "❌", str(code)


async def _get(client: httpx.AsyncClient, url: str) -> int | None:
    try:
        resp = await client.get(
            url, headers=HEADERS, timeout=20.0, follow_redirects=True
        )
        return resp.status_code
    except Exception:
        return None


def _norm_base(url: str) -> str:
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}"


async def main(names: list[str] | None = None) -> None:
    rows = []
    sites = _load_sites()
    if names:
        sites = {k: v for k, v in sites.items() if k in names}
    async with httpx.AsyncClient() as client:
        for name, config in sites.items():
            base = config["base_url"]
            search = config["search_url"].format(model=MODEL)
            robots = _norm_base(base) + "/robots.txt"

            base_code, base_desc = _status_emoji(await _get(client, base))
            search_code, search_desc = _status_emoji(await _get(client, search))
            robots_code, robots_desc = _status_emoji(await _get(client, robots))

            rows.append(
                {
                    "name": name,
                    "base": base,
                    "base_code": base_code,
                    "base_desc": base_desc,
                    "search": search,
                    "search_code": search_code,
                    "search_desc": search_desc,
                    "robots": robots,
                    "robots_code": robots_code,
                    "robots_desc": robots_desc,
                }
            )
            print(
                f"{name:<18} base={base_desc:<22} search={search_desc:<22} robots={robots_desc}",
                flush=True,
            )

    with open(Path(__file__).resolve().parent / "_url_check_results.json", "w") as f:
        json.dump(rows, f, indent=2, default=str)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check manufacturer URLs + robots.txt")
    parser.add_argument(
        "--names", nargs="*", default=None,
        help="Only check these manufacturer names (default: all)",
    )
    args = parser.parse_args()
    asyncio.run(main(names=args.names))
