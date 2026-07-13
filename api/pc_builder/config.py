"""api/pc_builder/config.py — GET /api/pc_builder/config"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
import json
from http.server import BaseHTTPRequestHandler
from lib.python.db import get_user_from_request
from lib.python.config_vercel import PC_BUILD_TYPES, PC_BUDGET_TIERS
from lib.python.storage import load_components_json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        user = get_user_from_request(dict(self.headers))
        if not user: self._json(401,{"detail":"Unauthorized"}); return
        self._json(200,{"build_types":PC_BUILD_TYPES,"budget_tiers":PC_BUDGET_TIERS,"component_count":len(load_components_json())})

    def _json(self, s, d):
        b=json.dumps(d,default=str).encode()
        self.send_response(s); self.send_header("Content-Type","application/json"); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers(); self.wfile.write(b)
    def do_OPTIONS(self):
        self.send_response(200); self.send_header("Access-Control-Allow-Origin","*"); self.send_header("Access-Control-Allow-Headers","Content-Type,Authorization"); self.end_headers()
