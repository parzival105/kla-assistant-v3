"""utils/helper.py"""
from __future__ import annotations
import re
from typing import Any
import pandas as pd
from lib.python.config_vercel import ALL_BRANCHES, EXCLUDED_BRANCH_COLS

def normalize_text(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()

def safe_numeric(series: pd.Series, fill_value: float = 0.0) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(fill_value)

def safe_divide(num: float, den: float, default: float = 0.0) -> float:
    try:
        return num / den if den != 0 else default
    except (TypeError, ZeroDivisionError):
        return default

def contains_any_keyword(text: Any, keywords: list) -> bool:
    norm = normalize_text(text)
    return any(normalize_text(kw) in norm for kw in keywords)

def detect_column_map(columns: list, aliases: dict) -> dict:
    norm_lookup = {normalize_text(c): c for c in columns}
    result = {}
    for canonical, variants in aliases.items():
        for v in variants:
            if normalize_text(v) in norm_lookup:
                result[canonical] = norm_lookup[normalize_text(v)]
                break
        if canonical in result:
            continue
        for norm_col, orig_col in norm_lookup.items():
            for v in variants:
                nv = normalize_text(v)
                if nv and (nv in norm_col or norm_col in nv):
                    result[canonical] = orig_col
                    break
            if canonical in result:
                break
    return result

def detect_branch_columns(columns: list) -> tuple:
    stock_cols, sales_cols = {}, {}
    sorted_branches = sorted(ALL_BRANCHES, key=len, reverse=True)
    for col in columns:
        norm = normalize_text(col)
        for branch in sorted_branches:
            b_lower = branch.lower()
            if re.search(rf"(?<![a-z0-9]){b_lower}(?![a-z0-9])", norm):
                is_sales = any(kw in norm for kw in ["terjual","sold","sales","jual"]) or col.endswith(".1")
                if is_sales:
                    sales_cols.setdefault(branch, col)
                else:
                    stock_cols.setdefault(branch, col)
                break
    return stock_cols, sales_cols
