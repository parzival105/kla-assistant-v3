"""
lib/python/storage.py
======================
Blob storage dual-mode: Supabase Storage atau lokal.

Kalau SUPABASE_URL dan SUPABASE_SERVICE_KEY terisi, file Excel stok dan hasil
analisis disimpan di Supabase Storage (bucket `kla-inventory`). Kalau tidak,
disimpan sebagai file di direktori sementara Vercel (/tmp/kla_data/blobs).
Signature fungsi dipertahankan agar API function lain tidak perlu diubah.

Catatan: mode lokal /tmp bersifat ephemeral per instance serverless. Untuk
penyimpanan permanen lintas instance, pakai mode Supabase.
"""
from __future__ import annotations
import os, json, logging
from typing import Optional

logger = logging.getLogger(__name__)

_DATA_DIR = os.environ.get("KLA_DATA_DIR", "/tmp/kla_data")
_BLOB_DIR = os.path.join(_DATA_DIR, "blobs")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
USE_SUPABASE = bool(SUPABASE_URL and SUPABASE_KEY)
BUCKET = "kla-inventory"


def _blob_path(path: str) -> str:
    return os.path.join(_BLOB_DIR, path)

def _sb_storage_headers(content_type="application/octet-stream"):
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": content_type,
    }

def upload_file(data: bytes, path: str, content_type: str = "application/octet-stream") -> str:
    """Simpan file ke storage. Mengembalikan path relatif."""
    if USE_SUPABASE:
        import requests
        url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{path}"
        r = requests.post(url, headers=_sb_storage_headers(content_type),
                          data=data, params={"upsert": "true"}, timeout=30)
        if r.status_code not in (200, 201):
            r = requests.put(url, headers=_sb_storage_headers(content_type),
                            data=data, timeout=30)
        r.raise_for_status()
        return path
    full = _blob_path(path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "wb") as f:
        f.write(data)
    return path

def download_file(path: str) -> Optional[bytes]:
    """Ambil file dari storage. None jika tidak ada."""
    if USE_SUPABASE:
        import requests
        url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{path}"
        r = requests.get(url, headers=_sb_storage_headers(), timeout=30)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.content
    full = _blob_path(path)
    if not os.path.exists(full):
        return None
    with open(full, "rb") as f:
        return f.read()

def save_analysis_pickle(analysis) -> str:
    """Serialize AnalysisResult dan simpan ke blob store lokal."""
    payload = {
        "df": analysis.df.to_json(orient="records"),
        "branch_long": analysis.branch_long_df.to_json(orient="records") if not analysis.branch_long_df.empty else "[]",
        "branch_summary": analysis.branch_summary_df.to_json(orient="records") if not analysis.branch_summary_df.empty else "[]",
        "transfer": analysis.transfer_df.to_json(orient="records") if not analysis.transfer_df.empty else "[]",
        "dead_stock": analysis.dead_stock_df.to_json(orient="records") if not analysis.dead_stock_df.empty else "[]",
        "stock_columns": analysis.stock_columns,
        "sales_columns": analysis.sales_columns,
        "revenue_summary": analysis.revenue_summary,
        "recommendations": analysis.recommendations,
        "rows_excluded": analysis.rows_excluded,
        "uploaded_at": analysis.uploaded_at,
    }
    data = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
    path = "analysis/current.json"
    upload_file(data, path, "application/json")
    return path

def load_analysis_from_storage() -> Optional[object]:
    """Load AnalysisResult dari blob store lokal."""
    import pandas as pd
    try:
        from api._shared.engine_imports import AnalysisResult
    except Exception:
        # Fallback import path
        import sys, os as _os
        sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), "../.."))
        from lib.python.inventory_engine import AnalysisResult

    data = download_file("analysis/current.json")
    if not data:
        return None

    try:
        payload = json.loads(data.decode("utf-8"))

        def _df(key):
            raw = payload.get(key, "[]")
            if raw == "[]" or not raw:
                return pd.DataFrame()
            try:
                return pd.DataFrame(json.loads(raw))
            except Exception:
                return pd.DataFrame()

        return AnalysisResult(
            df=_df("df"),
            branch_long_df=_df("branch_long"),
            branch_summary_df=_df("branch_summary"),
            transfer_df=_df("transfer"),
            dead_stock_df=_df("dead_stock"),
            purchasing_df=pd.DataFrame(),
            stock_columns=payload.get("stock_columns", {}),
            sales_columns=payload.get("sales_columns", {}),
            revenue_summary=payload.get("revenue_summary", {}),
            recommendations=payload.get("recommendations", []),
            rows_excluded=payload.get("rows_excluded", 0),
            uploaded_at=payload.get("uploaded_at", ""),
        )
    except Exception as e:
        logger.error(f"Failed to load analysis: {e}")
        return None

def save_components_json(components: list) -> None:
    """Simpan daftar komponen PC ke blob store lokal."""
    data = json.dumps(components, ensure_ascii=False, default=str).encode("utf-8")
    upload_file(data, "components/current.json", "application/json")

def load_components_json() -> list:
    """Load daftar komponen PC dari blob store lokal."""
    data = download_file("components/current.json")
    if not data:
        return []
    try:
        return json.loads(data.decode("utf-8"))
    except Exception:
        return []
