"""api/auth.py — All auth endpoints in one function."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from lib.python.db import (get_user_from_request, login as db_login, logout as db_logout,
    get_all_users, create_user, update_user, delete_user, log_action)
from lib.python.config_vercel import ROLE_LABELS, BRANCH_FULL_NAMES, AREA_MAP, ALL_BRANCHES

class handler(BaseHTTPRequestHandler):
    def _json(self, s, d):
        b = json.dumps(d, default=str).encode()
        self.send_response(s)
        self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Headers","Content-Type,Authorization")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Methods","GET,POST,PUT,DELETE,OPTIONS")
        self.send_header("Access-Control-Allow-Headers","Content-Type,Authorization")
        self.end_headers()

    def _path(self):
        parsed = urlparse(self.path)
        base = parsed.path.rstrip("/")
        sub = parse_qs(parsed.query).get("__sub", [""])[0]
        if base in ("/api/auth", "") and sub:
            base = "/api/auth/" + sub.rstrip("/")
        return base

    def _body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length)) if length else {}

    def _auth(self):
        user = get_user_from_request(dict(self.headers))
        if not user: self._json(401, {"detail":"Unauthorized"}); return None
        return user

    def _admin(self):
        user = self._auth()
        if not user: return None
        if user["role"] != "super_admin": self._json(403, {"detail":"Super Admin only"}); return None
        return user

    def _user_out(self, user):
        return {"id":user["id"],"username":user["username"],"full_name":user["full_name"],
                "role":user["role"],"role_label":ROLE_LABELS.get(user["role"],""),
                "branch":user.get("branch"),"area":user.get("area"),
                "branch_name":BRANCH_FULL_NAMES.get(user.get("branch",""),"")}

    def do_GET(self):
        p = self._path()
        if "/api/auth/me" in p:
            user = self._auth()
            if user: self._json(200, self._user_out(user))
        elif "/api/auth/users" in p:
            admin = self._admin()
            if not admin: return
            users = get_all_users()
            for u in users:
                u["branch_name"] = BRANCH_FULL_NAMES.get(u.get("branch",""),"")
                u["role_label"]  = ROLE_LABELS.get(u.get("role",""),"")
            self._json(200, {"users":users,
                "branches":[{"code":b,"name":BRANCH_FULL_NAMES[b]} for b in ALL_BRANCHES],
                "areas":list(AREA_MAP.keys()),
                "roles":[{"value":k,"label":v} for k,v in ROLE_LABELS.items()]})
        else:
            self._json(404, {"detail":"Not found"})

    def do_POST(self):
        p = self._path(); body = self._body()
        if "/api/auth/login" in p:
            ok, token, user = db_login(body.get("username",""), body.get("password",""))
            if not ok: self._json(401, {"detail":"Username atau password salah"}); return
            self._json(200, {"token":token,"user":self._user_out(user)})
        elif "/api/auth/logout" in p:
            auth = self.headers.get("Authorization","")
            if auth.startswith("Bearer "): db_logout(auth[7:])
            self._json(200, {"message":"Berhasil logout"})
        elif "/api/auth/users" in p:
            admin = self._admin()
            if not admin: return
            ok, msg = create_user(body["username"],body["password"],body["full_name"],
                                   body["role"],body.get("branch"),body.get("area"))
            self._json(200 if ok else 400, {"message":msg} if ok else {"detail":msg})
        else:
            self._json(404, {"detail":"Not found"})

    def do_PUT(self):
        admin = self._admin()
        if not admin: return
        body = self._body()
        uid  = body.get("id")
        ok, msg = update_user(uid, body["full_name"], body["role"],
                               body.get("branch"), body.get("area"),
                               body.get("is_active",True), body.get("new_password"))
        self._json(200 if ok else 400, {"message":msg} if ok else {"detail":msg})

    def do_DELETE(self):
        admin = self._admin()
        if not admin: return
        body = self._body(); uid = body.get("id")
        ok, msg = delete_user(uid)
        self._json(200 if ok else 400, {"message":msg} if ok else {"detail":msg})
