"""api/sales/query.py — POST /api/sales/query"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
import json
from http.server import BaseHTTPRequestHandler
from lib.python.db import get_user_from_request, has_analysis, log_action
from lib.python.storage import load_analysis_from_storage
from lib.python.intent import detect_intent
from lib.python.search import search_products
from lib.python.knowledge import ProductKnowledgeEngine
from lib.python.config_vercel import BRANCH_FULL_NAMES

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        user = get_user_from_request(dict(self.headers))
        if not user: self._json(401,{"detail":"Unauthorized"}); return
        length = int(self.headers.get("Content-Length",0))
        body   = json.loads(self.rfile.read(length))
        query  = body.get("query","").strip()
        top_n  = int(body.get("top_n",8))
        if not query: self._json(400,{"detail":"Query tidak boleh kosong"}); return
        if not has_analysis(): self._json(404,{"detail":"Belum ada data"}); return

        analysis = load_analysis_from_storage()
        df = analysis.df; stock_cols = analysis.stock_columns; role = user["role"]
        intent = detect_intent(query)
        log_action(user["id"],user["username"],"SALES_QUERY",f"[{intent.intent}] {query[:80]}")

        if intent.intent in ["PRODUCT_SEARCH","STOCK_CHECK","GENERAL"]:
            result = search_products(query=query, df=df, stock_columns=stock_cols, role=role,
                category_hint=intent.category_hint or "", brand_hint=intent.brand_hint or "",
                budget_hint=intent.budget_hint, use_case_hint=intent.use_case_hint or "", top_n=top_n)
            products = [{
                "nama_barang":p.nama_barang,"kategori":p.kategori,"segment":p.segment,"brand":p.brand,
                "harga_jual":p.harga_jual,"margin_persen":p.margin_persen,"hpp":p.hpp,
                "total_stok":p.total_stok,"runrate_bulanan":p.runrate_bulanan,
                "branch_stock":p.stock_by_branch,
                "branch_stock_named":{BRANCH_FULL_NAMES.get(b,b):q for b,q in p.stock_by_branch.items()},
                "score":p.score,
            } for p in result.products]
            self._json(200,{"intent":intent.intent,"mode":"product_search","products":products,
                "total_found":result.total_found,"notes":result.search_notes,
                "category_hint":intent.category_hint,"brand_hint":intent.brand_hint,
                "budget_hint":intent.budget_hint,"use_case_hint":intent.use_case_hint})

        elif intent.intent == "COMPATIBILITY":
            ke = ProductKnowledgeEngine()
            kr = ke.answer(query=query, df=df, stock_columns=stock_cols, role=role, category_hint=intent.category_hint or "")
            self._json(200,{"intent":intent.intent,"mode":"compatibility","answer":kr.answer,
                "recommended_products":kr.recommended_products,"upsell_suggestions":kr.upsell_suggestions,
                "compatibility_notes":kr.compatibility_notes,"category_hint":intent.category_hint})

        else:  # PC_BUILDER
            uc_map={"gaming":"Gaming Mid-range","editing":"Video Editing","kantor":"Office / Kerja","coding":"Coding / Development"}
            self._json(200,{"intent":intent.intent,"mode":"pc_builder",
                "suggested_build_type":uc_map.get(intent.use_case_hint or "","Office / Kerja"),
                "suggested_budget":intent.budget_hint,"brand_hint":intent.brand_hint})

    def _json(self, s, d):
        b=json.dumps(d,default=str).encode()
        self.send_response(s); self.send_header("Content-Type","application/json"); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers(); self.wfile.write(b)
    def do_OPTIONS(self):
        self.send_response(200); self.send_header("Access-Control-Allow-Origin","*"); self.send_header("Access-Control-Allow-Methods","POST,OPTIONS"); self.send_header("Access-Control-Allow-Headers","Content-Type,Authorization"); self.end_headers()
