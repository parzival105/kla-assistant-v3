"""api/export/excel.py — GET /api/export/excel"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
import io, json
from datetime import datetime
from http.server import BaseHTTPRequestHandler
import pandas as pd
from lib.python.db import get_user_from_request, has_analysis
from lib.python.storage import load_analysis_from_storage

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        user = get_user_from_request(dict(self.headers))
        if not user or user["role"]!="super_admin": self._err(403,"Super Admin only"); return
        if not has_analysis(): self._err(404,"Belum ada data"); return
        analysis = load_analysis_from_storage()
        df=analysis.df; s=analysis.revenue_summary
        rs=df[df["qty_restock"]>0].sort_values("nilai_restock",ascending=False).copy()
        rs["prioritas"]=range(1,len(rs)+1)

        def sel(df2,cols): return df2[[c for c in cols if c in df2.columns]]

        rev=pd.DataFrame([
            ("Total Inventory",f"Rp {s.get('inventory_value',0):,.0f}"),
            ("Dead Stock",f"Rp {s.get('dead_stock_value',0):,.0f}"),
            ("Dead Stock %",f"{s.get('dead_stock_pct',0):.1f}%"),
            ("Potensi Profit",f"Rp {s.get('potential_profit',0):,.0f}"),
            ("Total SKU",str(s.get('total_sku',0))),
        ],columns=["Metrik","Nilai"])
        recs=pd.DataFrame([{"Kategori":r.get("category"),"Prioritas":r.get("priority"),"Rekomendasi":r.get("text")} for r in analysis.recommendations])
        ic=["nama_barang","segment","kategori","runrate_bulanan","total_stok","min_stock","qty_restock","hpp","h1","h2","harga_rekomendasi","margin_persen"]
        bc=["branch","branch_name","area","health_score","rank","total_sku","inventory_value","dead_stock_value","critical_count"]
        dc=["nama_barang","total_stok","hpp","dead_stock_value","estimasi_bulan_tersimpan","rekomendasi_aksi","alasan"]

        sheets={
            "Executive Summary":rev,"AI Recommendation":recs,
            "Inventory Analysis":sel(df,ic),
            "Branch Analysis":sel(analysis.branch_summary_df,bc) if not analysis.branch_summary_df.empty else pd.DataFrame({"Info":["No data"]}),
            "Restock":sel(rs,ic+["prioritas"]),
            "Transfer":analysis.transfer_df if not analysis.transfer_df.empty else pd.DataFrame({"Info":["No transfers"]}),
            "Dead Stock":sel(analysis.dead_stock_df,dc) if not analysis.dead_stock_df.empty else pd.DataFrame({"Info":["No dead stock"]}),
        }
        buf=io.BytesIO()
        with pd.ExcelWriter(buf,engine="xlsxwriter") as writer:
            wb=writer.book
            hf=wb.add_format({"bold":True,"bg_color":"#431061","font_color":"#ffffff"})
            for sname,sdf in sheets.items():
                sdf.to_excel(writer,sheet_name=sname[:31],index=False)
                ws=writer.sheets[sname[:31]]
                for ci,col in enumerate(sdf.columns):
                    ws.write(0,ci,col,hf)
                    try: w=max(sdf[col].astype(str).map(len).max() if len(sdf) else 0,len(str(col)))
                    except: w=len(str(col))
                    ws.set_column(ci,ci,min(w+4,50))
        buf.seek(0)
        data=buf.read()
        ts=datetime.now().strftime("%Y%m%d_%H%M")
        self.send_response(200)
        self.send_header("Content-Type","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        self.send_header("Content-Disposition",f"attachment; filename=KLA_Report_{ts}.xlsx")
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Content-Length",str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _err(self,s,msg):
        b=json.dumps({"detail":msg}).encode()
        self.send_response(s); self.send_header("Content-Type","application/json"); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers(); self.wfile.write(b)
    def do_OPTIONS(self):
        self.send_response(200); self.send_header("Access-Control-Allow-Origin","*"); self.send_header("Access-Control-Allow-Headers","Content-Type,Authorization"); self.end_headers()
