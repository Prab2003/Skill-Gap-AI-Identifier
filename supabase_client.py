"""Tiny Supabase REST helper for Streamlit.

Relies only on httpx and st.secrets. Expected schema:
  table: user_state
  columns: profile_name (text, primary key), data (jsonb)

Configure in .streamlit/secrets.toml:
[supabase]
url = "https://YOUR_PROJECT_ID.supabase.co"
key = "YOUR_SERVICE_ROLE_OR_ANON_KEY"
"""

from __future__ import annotations

import json
from typing import Any, Dict

import httpx
import streamlit as st


@st.cache_resource(show_spinner=False)
def _client() -> httpx.Client | None:
    try:
        cfg = st.secrets.get("supabase", {})
    except Exception:
        # No secrets configured; treat Supabase as disabled
        return None
    url = cfg.get("url")
    key = cfg.get("key")
    if not url or not key:
        return None
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    return httpx.Client(base_url=url.rstrip("/"), headers=headers, timeout=10.0)


def supabase_enabled() -> bool:
    return _client() is not None


def load_user_state(profile_key: str) -> Dict[str, Any]:
    client = _client()
    if not client or not profile_key:
        return {}
    try:
        resp = client.get(
            "/rest/v1/user_state",
            params={"profile_name": f"eq.{profile_key}", "select": "data"},
        )
        if resp.status_code == 200:
            rows = resp.json()
            if rows:
                return rows[0].get("data", {}) or {}
    except Exception:
        # Fail silent; UI will remain local-only
        return {}
    return {}


def save_user_state(profile_key: str, data: Dict[str, Any]) -> bool:
    client = _client()
    if not client or not profile_key:
        return False
    payload = {"profile_name": profile_key, "data": data}
    try:
        resp = client.post(
            "/rest/v1/user_state",
            params={"on_conflict": "profile_name"},
            headers={"Prefer": "return=representation"},
            content=json.dumps([payload]),
        )
        return resp.status_code in (200, 201)
    except Exception:
        return False
