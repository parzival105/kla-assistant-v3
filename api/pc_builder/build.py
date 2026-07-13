"""api/pc_builder/build.py — POST /api/pc_builder/build"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
import json
from http.server import BaseHTTPRequestHandler
from lib.python.db import get_user_from_request, log_action
from lib.python.pc_builder import PCBuildEngine
from lib.python.storage import load_components_json

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        user = get_user_from_request(dict(self.headers))
        if not user: self._json(401,{"detail":"Unauthorized"}); return
        length = int(self.headers.get("Content-Length",0))
        body   = json.loads(self.rfile.read(length))
        build_type = body.get("build_type","Office / Kerja")
        budget     = float(body.get("budget",5_000_000))
        brand      = body.get("preferred_brand")
        notes      = body.get("customer_notes","")
        gen_ai     = body.get("generate_ai",True)

        comps = load_components_json()
        if not comps:
            self._json(503,{"detail":"Database komponen belum terisi. Admin perlu upload file stok."}); return

        eng   = PCBuildEngine()
        build = eng.build(build_type, budget, preferred_brand=brand)
        if not build:
            self._json(404,{"detail":"Tidak dapat membuat build. Stok tidak mencukupi atau budget terlalu rendah."}); return

        ai_explanation = ""
        if gen_ai:
            try:
                from lib.python.pc_builder_ai import generate_explanation
                ai_explanation = generate_explanation(build, notes)
            except: pass

        log_action(user["id"],user["username"],"PC_BUILD",f"{build_type} Rp{budget:,.0f}")
        self._json(200,{
            "build_type":build.build_type,"budget":build.budget,
            "total_price":build.total_price,"total_hpp":build.total_hpp,
            "margin_persen":build.margin_persen,"is_within_budget":build.is_within_budget,
            "sisa_budget":max(0,build.budget-build.total_price),
            "components":[{
                "kategori":c.kategori,"kategori_label":c.kategori_label,"nama":c.nama,
                "brand":c.brand,"harga_jual":c.selling_price,"h1":c.h1,"h2":c.h2,
                "stok_total":c.stok,"branch_stock":c.branch_stock,
            } for c in build.components],
            "compatibility_notes":build.compatibility_notes,
            "compatibility_warnings":build.compatibility_warnings,
            "build_warnings":build.build_warnings,
            "ai_explanation":ai_explanation,
        })

    def _json(self, s, d):
        b=json.dumps(d,default=str).encode()
        self.send_response(s); self.send_header("Content-Type","application/json"); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers(); self.wfile.write(b)
    def do_OPTIONS(self):
        self.send_response(200); self.send_header("Access-Control-Allow-Origin","*"); self.send_header("Access-Control-Allow-Methods","POST,OPTIONS"); self.send_header("Access-Control-Allow-Headers","Content-Type,Authorization"); self.end_headers()
