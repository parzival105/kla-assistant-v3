"""api/inventory.py — All inventory endpoints in one function."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import json, io, cgi
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import pandas as pd
from lib.python.db import get_user_from_request, save_analysis_meta, log_action, has_analysis, get_analysis_meta
from lib.python.storage import save_analysis_pickle, upload_file, save_components_json, load_analysis_from_storage
from lib.python.inventory_engine import InventoryEngine
from lib.python.helper import detect_branch_columns
from lib.python.pc_builder import load_components_from_stock
from lib.python.config_vercel import ROLE_STORE_LEADER, ROLE_AREA_MANAGER, AREA_MAP, ALL_BRANCHES

class handler(BaseHTTPRequestHandler):
    def _json(self, s, d):
        b = json.dumps(d, default=str).encode()
        self.send_response(s)
        self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Headers","Content-Type,Authorization")
        self.end_headers(); self.wfile.write(b)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Methods","GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers","Content-Type,Authorization")
        self.end_headers()

    def _path(self):
        parsed = urlparse(self.path)
        sub = parse_qs(parsed.query).get("__sub", [""])[0]
        if parsed.path.rstrip("/") in ("/api/inventory", "") and sub:
            return "/api/inventory/" + sub
        return parsed.path
    def _params(self): return parse_qs(urlparse(self.path).query)
    def _auth(self):
        user = get_user_from_request(dict(self.headers))
        if not user: self._json(401,{"detail":"Unauthorized"}); return None
        return user
    def _need_data(self):
        if not has_analysis(): self._json(404,{"detail":"Belum ada data. Upload file stok."}); return False
        return True

    def do_POST(self):
        user = self._auth()
        if not user: return
        if user["role"] != "super_admin": self._json(403,{"detail":"Super Admin only"}); return
        try:
            ct = self.headers.get("Content-Type","")
            ln = int(self.headers.get("Content-Length",0))
            raw = self.rfile.read(ln)
            env = {"REQUEST_METHOD":"POST","CONTENT_TYPE":ct,"CONTENT_LENGTH":str(ln)}
            form = cgi.FieldStorage(fp=io.BytesIO(raw), environ=env, keep_blank_values=True)
            fi = form.get("file")
            if not fi or not hasattr(fi,"file"): self._json(400,{"detail":"File tidak ditemukan"}); return
            fname = fi.filename or "stock.xlsx"
            fbytes = fi.file.read()
            engine = InventoryEngine()
            result = engine.load_file(io.BytesIO(fbytes))
            storage_path = save_analysis_pickle(result)
            save_analysis_meta(fname, user["username"], len(result.df), storage_path)
            upload_file(fbytes, "stock/current.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            raw_df = pd.read_excel(io.BytesIO(fbytes), engine="openpyxl")
            sc = {}
            for col in raw_df.columns:
                cn = col.strip().upper()
                for br in ALL_BRANCHES:
                    if cn == br and not col.endswith(".1"): sc[br]=col; break
            n, comps = load_components_from_stock(raw_df, sc)
            save_components_json(comps)
            log_action(user["id"],user["username"],"UPLOAD_STOCK",f"File:{fname} SKU:{len(result.df)}")
            self._json(200,{"message":"Upload berhasil","sku_count":len(result.df),
                "rows_excluded":result.rows_excluded,"components_loaded":n,"filename":fname})
        except Exception as e:
            import traceback
            self._json(500,{"detail":str(e),"trace":traceback.format_exc()[-800:]})

    def do_GET(self):
        user = self._auth()
        if not user: return
        p = self._path(); params = self._params()

        if "/status" in p:
            meta = get_analysis_meta()
            if not meta: self._json(200,{"has_data":False}); return
            self._json(200,{"has_data":True,"filename":meta.get("filename"),"uploaded_by":meta.get("uploaded_by"),"uploaded_at":meta.get("uploaded_at"),"sku_count":meta.get("sku_count",0)})
            return

        if not self._need_data(): return
        analysis = load_analysis_from_storage()
        if not analysis: self._json(500,{"detail":"Gagal memuat data"}); return
        df = analysis.df; role = user["role"]

        if "/summary" in p:
            s = analysis.revenue_summary
            cc = df["kategori"].value_counts().to_dict() if "kategori" in df.columns else {}
            cv = df.groupby("kategori")["nilai_inventory"].sum().to_dict() if "kategori" in df.columns and "nilai_inventory" in df.columns else {}
            self._json(200,{"revenue_summary":s,"category_counts":cc,"category_values":cv,
                "transfer_count":len(analysis.transfer_df) if not analysis.transfer_df.empty else 0,
                "restock_count":int((df["qty_restock"]>0).sum()) if "qty_restock" in df.columns else 0})

        elif "/products" in p:
            search=params.get("search",[""])[0]; kat=params.get("kategori",[""])[0]
            page=int(params.get("page",["1"])[0]); pp=int(params.get("per_page",["50"])[0])
            f=df.copy()
            if search: f=f[f["nama_barang"].str.contains(search,case=False,na=False)]
            if kat and kat!="Semua": f=f[f["kategori"]==kat]
            total=len(f); start=(page-1)*pp; pf=f.iloc[start:start+pp]
            cols=[c for c in ["nama_barang","segment","brand","kategori","runrate_bulanan","total_stok","min_stock","coverage_month","stock_day","qty_restock","hpp","h1","h2","harga_rekomendasi","margin_persen","nilai_inventory"] if c in pf.columns]
            self._json(200,{"total":total,"page":page,"per_page":pp,"products":pf[cols].fillna(0).to_dict(orient="records"),"filters":{"kategoris":["Very Fast","Fast","Slow","Dead Stock"]}})

        elif "/transfer" in p:
            tf=analysis.transfer_df.copy()
            if tf.empty: self._json(200,{"items":[],"summary":{"total_transactions":0,"total_value":0,"areas":[]}}); return
            if role==ROLE_STORE_LEADER and user.get("branch"):
                br=user["branch"]; tf=tf[(tf["dari_cabang"]==br)|(tf["ke_cabang"]==br)]
            elif role==ROLE_AREA_MANAGER and user.get("area"):
                tf=tf[tf["area"]==user["area"]]
            self._json(200,{"items":tf.fillna(0).to_dict(orient="records"),"summary":{"total_transactions":len(tf),"total_value":float(tf["nilai_transfer"].sum()),"areas":tf["area"].unique().tolist()}})

        elif "/restock" in p:
            rs=df[df["qty_restock"]>0].sort_values("nilai_restock",ascending=False).copy()
            rs["prioritas"]=range(1,len(rs)+1)
            cols=[c for c in ["prioritas","nama_barang","kategori","runrate_bulanan","total_stok","min_stock","qty_restock","hpp","nilai_restock"] if c in rs.columns]
            self._json(200,{"items":rs[cols].fillna(0).to_dict(orient="records"),"summary":{"sku_count":len(rs),"total_qty":float(rs["qty_restock"].sum()),"total_value":float(rs["nilai_restock"].sum())}})

        elif "/deadstock" in p:
            dead=analysis.dead_stock_df
            if dead.empty: self._json(200,{"items":[],"total_value":0,"by_action":{}}); return
            cols=[c for c in ["nama_barang","segment","kategori","total_stok","hpp","dead_stock_value","estimasi_bulan_tersimpan","rekomendasi_aksi","alasan"] if c in dead.columns]
            by_act=dead.groupby("rekomendasi_aksi").agg(count=("nama_barang","count"),value=("dead_stock_value","sum")).to_dict(orient="index")
            self._json(200,{"items":dead[cols].fillna(0).to_dict(orient="records"),"total_value":float(dead["dead_stock_value"].sum()),"by_action":by_act})

        elif "/recommendations" in p:
            self._json(200,{"recommendations":analysis.recommendations})

        elif "/pricing" in p:
            sh=role in ["super_admin","area_manager"]; sm=role in ["super_admin","area_manager","store_leader"]
            cols=["nama_barang","segment","kategori","runrate_bulanan","h1","h2","hd","harga_rekomendasi","margin_persen"]
            if sh: cols+=["hpp","margin_nominal"]
            av=[c for c in cols if c in df.columns]
            data=df[av].fillna(0).to_dict(orient="records")
            if not sm:
                for row in data: row.pop("margin_persen",None)
            self._json(200,{"items":data,"show_hpp":sh,"show_margin":sm})

        else:
            self._json(404,{"detail":"Endpoint not found"})
