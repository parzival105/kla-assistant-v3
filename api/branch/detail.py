"""api/branch/detail.py — GET /api/branch/detail?code=SMG"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from lib.python.db import get_user_from_request, has_analysis
from lib.python.storage import load_analysis_from_storage
from lib.python.config_vercel import BRANCH_FULL_NAMES, ROLE_STORE_LEADER, ROLE_AREA_MANAGER, AREA_MAP

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        user = get_user_from_request(dict(self.headers))
        if not user: self._json(401,{"detail":"Unauthorized"}); return
        params = parse_qs(urlparse(self.path).query)
        branch_code = params.get("code",[""])[0]
        if not branch_code: self._json(400,{"detail":"Parameter 'code' wajib"}); return

        role=user["role"]; user_branch=user.get("branch"); user_area=user.get("area")
        if role==ROLE_STORE_LEADER and user_branch!=branch_code:
            self._json(403,{"detail":"Akses ditolak"}); return
        if role==ROLE_AREA_MANAGER and user_area:
            if branch_code not in AREA_MAP.get(user_area,[]):
                self._json(403,{"detail":"Cabang bukan dalam area Anda"}); return

        if not has_analysis(): self._json(404,{"detail":"Belum ada data"}); return
        analysis = load_analysis_from_storage()
        bl = analysis.branch_long_df
        bsum = analysis.branch_summary_df
        detail = bl[bl["branch"]==branch_code].copy() if not bl.empty else bl
        br_row = bsum[bsum["branch"]==branch_code]
        summary = {k:(float(v) if hasattr(v,"item") else v) for k,v in br_row.iloc[0].to_dict().items()} if not br_row.empty else {}
        cols=[c for c in ["nama_barang","kategori","stok_cabang","terjual_cabang","runrate_cabang","min_stock_cabang","stock_day_cabang","status"] if c in detail.columns]
        self._json(200,{
            "branch_code":branch_code,"branch_name":BRANCH_FULL_NAMES.get(branch_code,branch_code),
            "products":detail[cols].fillna(0).to_dict(orient="records") if not detail.empty else [],
            "summary":summary,
        })

    def _json(self, s, d):
        b=json.dumps(d,default=str).encode()
        self.send_response(s); self.send_header("Content-Type","application/json"); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers(); self.wfile.write(b)
    def do_OPTIONS(self):
        self.send_response(200); self.send_header("Access-Control-Allow-Origin","*"); self.send_header("Access-Control-Allow-Headers","Content-Type,Authorization"); self.end_headers()
