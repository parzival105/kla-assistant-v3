"""utils/formatter.py"""
from __future__ import annotations
from typing import Any
from lib.python.config_vercel import CATEGORY_COLORS, ROLE_COLORS, ROLE_LABELS

def format_rupiah(value: float) -> str:
    try: return f"Rp {value:,.0f}"
    except: return "Rp 0"

def format_rupiah_short(value: float) -> str:
    try:
        s = "-" if value < 0 else ""
        v = abs(value)
        if v >= 1_000_000_000: return f"{s}Rp {v/1_000_000_000:.2f}M"
        if v >= 1_000_000:     return f"{s}Rp {v/1_000_000:.1f}Jt"
        if v >= 1_000:         return f"{s}Rp {v/1_000:.0f}Rb"
        return f"{s}Rp {v:,.0f}"
    except: return "Rp 0"

def format_percent(value: float, decimals: int = 1) -> str:
    try: return f"{value:.{decimals}f}%"
    except: return "0%"

def format_number(value: float, decimals: int = 0) -> str:
    try: return f"{value:,.{decimals}f}"
    except: return "0"

def format_days(value: float) -> str:
    try: return "999+ hari" if value >= 999 else f"{value:,.0f} hari"
    except: return "N/A"

def category_badge_html(category: str) -> str:
    color = CATEGORY_COLORS.get(category, "#94a3b8")
    return f'<span style="display:inline-block;padding:2px 10px;border-radius:20px;font-size:11px;font-weight:600;background:{color}22;color:{color};border:1px solid {color}55;">{category}</span>'

def role_badge_html(role: str) -> str:
    color = ROLE_COLORS.get(role, "#94a3b8")
    label = ROLE_LABELS.get(role, role)
    return f'<span style="display:inline-block;padding:2px 10px;border-radius:20px;font-size:11px;font-weight:600;background:{color}22;color:{color};border:1px solid {color}55;">{label}</span>'

def health_score_label(score: float) -> tuple:
    if score >= 80: return "Sangat Sehat", "#059669"
    if score >= 60: return "Sehat", "#7c3aed"
    if score >= 40: return "Perlu Perhatian", "#d97706"
    return "Bermasalah", "#dc2626"

def truncate_text(value: Any, max_len: int = 35) -> str:
    t = str(value)
    return t if len(t) <= max_len else t[:max_len-1] + "…"
