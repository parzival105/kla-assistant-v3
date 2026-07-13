"""
lib/python/db.py
=================
Data layer dual-mode: Supabase atau lokal.

Kalau environment variable SUPABASE_URL dan SUPABASE_SERVICE_KEY terisi, semua
data (users, audit log, metadata analisis, riwayat build) disimpan di Supabase
lewat REST API (PostgREST). Kalau tidak, data disimpan sebagai file JSON di
direktori sementara Vercel (/tmp/kla_data) dengan admin default yang di-seed
otomatis, cocok untuk demo tanpa backend eksternal.

Auth memakai token HMAC stateless di kedua mode, jadi tidak perlu tabel
sessions dan token bisa diverifikasi oleh function mana pun tanpa storage
bersama, asal JWT_SECRET sama.

Setiap API function import dari sini, signature fungsi tidak berubah.
"""
from __future__ import annotations
import os, json, hashlib, hmac, base64, logging, threading
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

JWT_SECRET   = os.environ.get("JWT_SECRET", "kla-default-secret-2025")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
USE_SUPABASE = bool(SUPABASE_URL and SUPABASE_KEY)

_DATA_DIR = os.environ.get("KLA_DATA_DIR", "/tmp/kla_data")
_LOCK = threading.RLock()


# ── Supabase REST helpers ─────────────────────────────────────────────────────

def _sb_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

def _sb_get(table: str, params: dict = {}) -> list:
    import requests
    r = requests.get(f"{SUPABASE_URL}/rest/v1/{table}",
                     headers=_sb_headers(), params=params, timeout=10)
    r.raise_for_status()
    return r.json()

def _sb_post(table: str, data: dict) -> dict:
    import requests
    r = requests.post(f"{SUPABASE_URL}/rest/v1/{table}",
                      headers=_sb_headers(), json=data, timeout=10)
    r.raise_for_status()
    result = r.json()
    return result[0] if isinstance(result, list) and result else result

def _sb_patch(table: str, filters: dict, data: dict) -> list:
    import requests
    params = {k: f"eq.{v}" for k, v in filters.items()}
    r = requests.patch(f"{SUPABASE_URL}/rest/v1/{table}",
                       headers=_sb_headers(), params=params, json=data, timeout=10)
    r.raise_for_status()
    return r.json()

def _sb_delete(table: str, filters: dict) -> None:
    import requests
    params = {k: f"eq.{v}" for k, v in filters.items()}
    r = requests.delete(f"{SUPABASE_URL}/rest/v1/{table}",
                        headers=_sb_headers(), params=params, timeout=10)
    r.raise_for_status()


# ── Local file store helpers ──────────────────────────────────────────────────

def _path(name: str) -> str:
    return os.path.join(_DATA_DIR, name)

def _read_json(name: str, default):
    try:
        with open(_path(name), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def _write_json(name: str, data) -> None:
    try:
        os.makedirs(_DATA_DIR, exist_ok=True)
        with open(_path(name), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, default=str)
    except Exception as e:
        logger.error(f"write {name} failed: {e}")

def _next_id(rows: list) -> int:
    return (max((r.get("id", 0) for r in rows), default=0) + 1) if rows else 1


# ── Password ──────────────────────────────────────────────────────────────────

def hash_password(pw: str) -> str:
    return hashlib.sha256(f"kla_salt_{pw}_kla2025".encode()).hexdigest()

def verify_password(pw: str, hashed: str) -> bool:
    return hash_password(pw) == hashed


# ── Local users seed ──────────────────────────────────────────────────────────

def _seed_users() -> list:
    return [{
        "id": 1,
        "username": "admin",
        "password_hash": hash_password("admin123"),
        "full_name": "Super Admin KLA",
        "role": "super_admin",
        "branch": None,
        "area": None,
        "is_active": True,
        "created_at": "2026-01-01T00:00:00",
        "last_login": None,
    }]

def _load_users() -> list:
    users = _read_json("users.json", None)
    if not users:
        users = _seed_users()
        _write_json("users.json", users)
    return users

def _save_users(users: list) -> None:
    _write_json("users.json", users)


# ── Stateless signed token ────────────────────────────────────────────────────
# Setiap serverless function punya /tmp terpisah, jadi session tidak bisa
# disimpan bersama. Token menyimpan identitas user dan diverifikasi lewat
# JWT_SECRET yang sama di semua function, tanpa perlu storage bersama.

def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")

def _b64d(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))

def _sign(payload_b64: str) -> str:
    sig = hmac.new(JWT_SECRET.encode(), payload_b64.encode(), hashlib.sha256).digest()
    return _b64e(sig)

def _make_token(user: dict) -> str:
    payload = {
        "uid": user["id"],
        "username": user["username"],
        "full_name": user["full_name"],
        "role": user["role"],
        "branch": user.get("branch"),
        "area": user.get("area"),
        "exp": (datetime.utcnow() + timedelta(hours=8)).timestamp(),
    }
    payload_b64 = _b64e(json.dumps(payload, separators=(",", ":")).encode())
    return f"{payload_b64}.{_sign(payload_b64)}"

def validate_token(token: str) -> Optional[dict]:
    if not token or "." not in token:
        return None
    try:
        payload_b64, sig = token.rsplit(".", 1)
        if not hmac.compare_digest(sig, _sign(payload_b64)):
            return None
        payload = json.loads(_b64d(payload_b64))
        if float(payload.get("exp", 0)) < datetime.utcnow().timestamp():
            return None
        return {
            "id": payload["uid"],
            "username": payload["username"],
            "full_name": payload["full_name"],
            "role": payload["role"],
            "branch": payload.get("branch"),
            "area": payload.get("area"),
            "is_active": True,
        }
    except Exception:
        return None

def logout(token: str) -> None:
    # Token stateless tidak bisa dicabut di server. Logout ditangani di client
    # dengan menghapus cookie token.
    return None

def get_user_from_request(headers: dict) -> Optional[dict]:
    auth = headers.get("authorization", "") or headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    return validate_token(auth[7:])


# ── Auth ─────────────────────────────────────────────────────────────────────

def login(username: str, password: str) -> tuple[bool, Optional[str], Optional[dict]]:
    uname = username.lower().strip()
    if USE_SUPABASE:
        rows = _sb_get("users", {"username": f"eq.{uname}", "is_active": "eq.true"})
        if not rows:
            return False, None, None
        user = rows[0]
        if not verify_password(password, user["password_hash"]):
            return False, None, None
        token = _make_token(user)
        try:
            _sb_patch("users", {"id": user["id"]},
                      {"last_login": datetime.utcnow().isoformat()})
        except Exception:
            pass
        log_action(user["id"], user["username"], "LOGIN", "")
        return True, token, user

    with _LOCK:
        users = _load_users()
        user = next((u for u in users
                     if u["username"] == uname and u.get("is_active")), None)
        if not user or not verify_password(password, user["password_hash"]):
            return False, None, None
        token = _make_token(user)
        user["last_login"] = datetime.utcnow().isoformat()
        _save_users(users)
        log_action(user["id"], user["username"], "LOGIN", "")
        return True, token, user

def get_all_users() -> list:
    if USE_SUPABASE:
        return _sb_get("users", {"order": "role.asc,full_name.asc"})
    users = _load_users()
    return sorted(users, key=lambda u: (u.get("role", ""), u.get("full_name", "")))

def create_user(username, password, full_name, role, branch=None, area=None):
    uname = username.lower().strip()
    if USE_SUPABASE:
        try:
            _sb_post("users", {
                "username": uname,
                "password_hash": hash_password(password),
                "full_name": full_name.strip(),
                "role": role, "branch": branch, "area": area,
                "is_active": True,
                "created_at": datetime.utcnow().isoformat(),
            })
            return True, f"User '{username}' berhasil dibuat."
        except Exception as e:
            msg = str(e)
            if "unique" in msg.lower() or "duplicate" in msg.lower() or "23505" in msg:
                return False, f"Username '{username}' sudah digunakan."
            return False, msg

    with _LOCK:
        users = _load_users()
        if any(u["username"] == uname for u in users):
            return False, f"Username '{username}' sudah digunakan."
        users.append({
            "id": _next_id(users),
            "username": uname,
            "password_hash": hash_password(password),
            "full_name": full_name.strip(),
            "role": role, "branch": branch, "area": area,
            "is_active": True,
            "created_at": datetime.utcnow().isoformat(),
            "last_login": None,
        })
        _save_users(users)
        return True, f"User '{username}' berhasil dibuat."

def update_user(user_id, full_name, role, branch=None, area=None, is_active=True, new_password=None):
    data = {"full_name": full_name, "role": role,
            "branch": branch, "area": area, "is_active": is_active}
    if new_password:
        data["password_hash"] = hash_password(new_password)
    if USE_SUPABASE:
        try:
            rows = _sb_patch("users", {"id": user_id}, data)
            if not rows:
                return False, "User tidak ditemukan."
            return True, "User berhasil diupdate."
        except Exception as e:
            return False, str(e)

    with _LOCK:
        users = _load_users()
        user = next((u for u in users if u["id"] == user_id), None)
        if not user:
            return False, "User tidak ditemukan."
        user.update(data)
        _save_users(users)
        return True, "User berhasil diupdate."

def delete_user(user_id):
    # Soft delete: nonaktifkan, jangan hard delete (jaga audit trail).
    if USE_SUPABASE:
        try:
            rows = _sb_patch("users", {"id": user_id}, {"is_active": False})
            if not rows:
                return False, "User tidak ditemukan."
            return True, "User dinonaktifkan."
        except Exception as e:
            return False, str(e)

    with _LOCK:
        users = _load_users()
        user = next((u for u in users if u["id"] == user_id), None)
        if not user:
            return False, "User tidak ditemukan."
        user["is_active"] = False
        _save_users(users)
        return True, "User dinonaktifkan."

def log_action(user_id, username, action, detail=""):
    try:
        if USE_SUPABASE:
            _sb_post("audit_log", {
                "user_id": user_id, "username": username,
                "action": action, "detail": detail,
                "created_at": datetime.utcnow().isoformat(),
            })
            return
        with _LOCK:
            logs = _read_json("audit.json", [])
            logs.append({
                "user_id": user_id, "username": username,
                "action": action, "detail": detail,
                "created_at": datetime.utcnow().isoformat(),
            })
            _write_json("audit.json", logs[-500:])
    except Exception:
        pass


# ── Analysis Store ────────────────────────────────────────────────────────────

def save_analysis_meta(filename: str, uploaded_by: str, sku_count: int, storage_path: str):
    record = {
        "id": 1,
        "filename": filename,
        "uploaded_by": uploaded_by,
        "sku_count": sku_count,
        "storage_path": storage_path,
        "uploaded_at": datetime.utcnow().isoformat(),
    }
    if USE_SUPABASE:
        try:
            _sb_delete("analysis_store", {"id": 1})
        except Exception:
            pass
        _sb_post("analysis_store", record)
        return
    _write_json("analysis_meta.json", record)

def get_analysis_meta() -> Optional[dict]:
    if USE_SUPABASE:
        rows = _sb_get("analysis_store", {"id": "eq.1"})
        return rows[0] if rows else None
    return _read_json("analysis_meta.json", None)

def has_analysis() -> bool:
    return get_analysis_meta() is not None


# ── PC Build History ──────────────────────────────────────────────────────────

def save_build_history(user_id, branch, build_name, build_type, budget, total_price, components, ai_notes):
    record = {
        "user_id": user_id, "branch": branch,
        "build_name": build_name, "build_type": build_type,
        "budget": budget, "total_price": total_price,
        "components": json.dumps(components, ensure_ascii=False),
        "ai_notes": (ai_notes or "")[:500],
        "created_at": datetime.utcnow().isoformat(),
    }
    if USE_SUPABASE:
        _sb_post("build_history", record)
        return
    with _LOCK:
        hist = _read_json("build_history.json", [])
        record["id"] = _next_id(hist)
        hist.insert(0, record)
        _write_json("build_history.json", hist[:100])

def get_build_history(user_id=None, limit=20) -> list:
    if USE_SUPABASE:
        params = {"order": "created_at.desc", "limit": str(limit)}
        if user_id:
            params["user_id"] = f"eq.{user_id}"
        return _sb_get("build_history", params)
    hist = _read_json("build_history.json", [])
    if user_id:
        hist = [h for h in hist if h.get("user_id") == user_id]
    return hist[:limit]
