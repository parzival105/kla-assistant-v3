"""api/branch/summary.py"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
import json
from http.server import BaseHTTPRequestHandler
from lib.python.db import get_user_from_request, has_analysis
from lib.python.storage import load_analysis_from_storage
from lib.python.config_vercel import ROLE_STORE_LEADER, ROLE_AREA_MANAGER, AREA_MAP

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        user = get_user_from_request(dict(self.headers))
        if not user: self._json(401,{"detail":"Unauthorized"}); return
        if not has_analysis(): self._json(404,{"detail":"Belum ada data"}); return
        analysis = load_analysis_from_storage()
        bsum = analysis.branch_summary_df.copy()
        if bsum.empty: self._json(200,{"branches":[]}); return
        role=user["role"]; branch=user.get("branch"); area=user.get("area")
        if role==ROLE_STORE_LEADER and branch:
            bsum=bsum[bsum["branch"]==branch]
        elif role==ROLE_AREA_MANAGER and area:
            bsum=bsum[bsum["branch"].isin(AREA_MAP.get(area,[]))]
        cols=[c for c in ["branch","branch_name","area","rank","health_score","total_sku","total_stok","inventory_value","dead_stock_value","fast_moving_sku","dead_stock_sku","overstock_count","normal_count","understock_count","critical_count"] if c in bsum.columns]
        self._json(200,{"branches":bsum[cols].fillna(0).to_dict(orient="records")})

    def _json(self, s, d):
        b=json.dumps(d,default=str).encode()
        self.send_response(s); self.send_header("Content-Type","application/json"); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers(); self.wfile.write(b)
    def do_OPTIONS(self):
        self.send_response(200); self.send_header("Access-Control-Allow-Origin","*"); self.send_header("Access-Control-Allow-Headers","Content-Type,Authorization"); self.end_headers()
