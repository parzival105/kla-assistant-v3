"""modules/inventory/engine.py — Full inventory pipeline."""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Optional, BinaryIO
import numpy as np
import pandas as pd
from lib.python.config_vercel import (
    COLUMN_ALIASES, EXCLUDED_KEYWORDS, RUNRATE_HISTORY_MONTHS,
    CATEGORY_THRESHOLDS, AREA_MAP, BRANCH_TO_AREA, BRANCH_FULL_NAMES,
    DEAD_STOCK_BUCKETS, HEALTH_SCORE_WEIGHTS,
    OVERSTOCK_RATIO, UNDERSTOCK_RATIO, CRITICAL_STOCK_DAY,
    PRIORITY_A_RUNRATE_MIN, PRIORITY_A_STOCKDAY_MAX, PRIORITY_A_MARGIN_MIN,
)
from lib.python.helper import detect_column_map, detect_branch_columns, safe_numeric, safe_divide, contains_any_keyword
from lib.python.formatter import format_rupiah_short

logger = logging.getLogger(__name__)
_MULT = {t.name: t.min_stock_multiplier for t in CATEGORY_THRESHOLDS}

@dataclass
class AnalysisResult:
    df: pd.DataFrame
    branch_long_df: pd.DataFrame
    branch_summary_df: pd.DataFrame
    transfer_df: pd.DataFrame
    dead_stock_df: pd.DataFrame
    purchasing_df: pd.DataFrame
    revenue_summary: dict
    recommendations: list
    stock_columns: dict = field(default_factory=dict)
    sales_columns: dict = field(default_factory=dict)
    rows_excluded: int = 0
    warnings: list = field(default_factory=list)
    uploaded_at: str = ""

class InventoryEngine:
    def load_file(self, uploaded_file: BinaryIO) -> AnalysisResult:
        from datetime import datetime
        raw = pd.read_excel(uploaded_file, engine="openpyxl")
        col_map = detect_column_map(list(raw.columns), COLUMN_ALIASES)
        stock_cols, sales_cols = detect_branch_columns(list(raw.columns))
        missing = [f for f in ["hpp","total_stok","total_terjual"] if f not in col_map]
        if missing:
            raise ValueError(f"Kolom wajib tidak terdeteksi: {missing}. Pastikan file memiliki HPP, Total Stoks, Total Terjual.")
        rename_map = {actual: canonical for canonical, actual in col_map.items()}
        df = raw.rename(columns=rename_map).copy()
        if "nama_barang" not in df.columns:
            df = df.rename(columns={df.columns[0]: "nama_barang"})
        rows_before = len(df)
        df = self._filter_exclusions(df)
        rows_excluded = rows_before - len(df)
        df = self._coerce_numeric(df, stock_cols, sales_cols)
        df = df.reset_index(drop=True)
        df = self._runrate(df)
        df = self._categorize(df)
        df = self._min_stock(df)
        df = self._inventory_value(df)
        df = self._restock(df)
        df = self._pricing(df)
        df = self._profit(df)
        branch_long = self._build_branch_long(df, stock_cols, sales_cols)
        branch_long = self._branch_status(branch_long)
        branch_summary = self._branch_summary(branch_long)
        branch_summary = self._health_scores(branch_summary)
        transfer_df = self._transfers(branch_long)
        raw_cols = list(set(stock_cols.values()) | set(sales_cols.values()))
        df = df.drop(columns=[c for c in raw_cols if c in df.columns])
        dead_df = self._dead_stock(df)
        purchasing_df = self._purchasing(df)
        revenue = self._revenue_summary(df, dead_df, transfer_df)
        recs = self._recommendations(df, dead_df, transfer_df, purchasing_df, branch_summary, revenue)
        return AnalysisResult(
            df=df, branch_long_df=branch_long, branch_summary_df=branch_summary,
            transfer_df=transfer_df, dead_stock_df=dead_df, purchasing_df=purchasing_df,
            revenue_summary=revenue, recommendations=recs,
            stock_columns=stock_cols, sales_columns=sales_cols,
            rows_excluded=rows_excluded, uploaded_at=datetime.now().isoformat()
        )

    @staticmethod
    def _filter_exclusions(df):
        name_col = "nama_barang" if "nama_barang" in df.columns else df.columns[0]
        mask = ~df[name_col].apply(lambda x: contains_any_keyword(x, EXCLUDED_KEYWORDS))
        if "kategori_produk" in df.columns:
            mask &= ~df["kategori_produk"].apply(lambda x: contains_any_keyword(x, EXCLUDED_KEYWORDS))
        return df[mask].copy()

    @staticmethod
    def _coerce_numeric(df, stock_cols, sales_cols):
        for col in ["hpp","hd","h1","h2","total_stok","total_terjual"]:
            if col in df.columns: df[col] = safe_numeric(df[col])
        for col in list(stock_cols.values()) + list(sales_cols.values()):
            if col in df.columns: df[col] = safe_numeric(df[col])
        return df

    @staticmethod
    def _runrate(df):
        df = df.copy()
        df["runrate_bulanan"] = (safe_numeric(df["total_terjual"]) / RUNRATE_HISTORY_MONTHS).round(2)
        return df

    @staticmethod
    def _categorize(df):
        df = df.copy()
        def _cat(rr):
            for t in CATEGORY_THRESHOLDS:
                if t.min_runrate <= rr < t.max_runrate: return t.name
            return "Dead Stock"
        df["kategori"] = df["runrate_bulanan"].apply(_cat)
        return df

    @staticmethod
    def _min_stock(df):
        df = df.copy()
        df["min_stock"] = df.apply(lambda r: round(r["runrate_bulanan"] * _MULT.get(r["kategori"],0)), axis=1)
        df["coverage_month"] = df.apply(
            lambda r: round(safe_divide(r["total_stok"], r["runrate_bulanan"], 999.0 if r["total_stok"]>0 else 0.0), 2), axis=1)
        df["stock_day"] = (df["coverage_month"] * 30).round(0)
        return df

    @staticmethod
    def _inventory_value(df):
        df = df.copy(); df["nilai_inventory"] = df["total_stok"] * df["hpp"]; return df

    @staticmethod
    def _restock(df):
        df = df.copy()
        df["qty_restock"] = (df["min_stock"] - df["total_stok"]).clip(lower=0)
        df["nilai_restock"] = df["qty_restock"] * df["hpp"]
        return df

    @staticmethod
    def _pricing(df):
        df = df.copy()
        tier = {"Very Fast":"h2","Fast":"h1","Slow":"hd","Dead Stock":"hd"}
        def _price(row):
            col = tier.get(row["kategori"],"hd")
            val = row.get(col, 0)
            if pd.isna(val) or val <= 0:
                for fb in ["hd","h1","h2"]:
                    fv = row.get(fb, 0)
                    if fv and fv > 0: return fv
                return row.get("hpp", 0)
            return val
        df["harga_rekomendasi"] = df.apply(_price, axis=1)
        df["margin_nominal"] = df["harga_rekomendasi"] - df["hpp"]
        df["margin_persen"] = np.where(df["harga_rekomendasi"]>0,
            (df["margin_nominal"]/df["harga_rekomendasi"]*100).round(2), 0.0)
        return df

    @staticmethod
    def _profit(df):
        df = df.copy(); df["potensi_profit"] = df["margin_nominal"] * df["total_stok"]; return df

    def _build_branch_long(self, df, stock_cols, sales_cols):
        if not stock_cols:
            return pd.DataFrame(columns=["nama_barang","kategori","hpp","branch","area",
                "stok_cabang","terjual_cabang","runrate_cabang","min_stock_cabang","coverage_cabang","stock_day_cabang"])
        name_col = "nama_barang" if "nama_barang" in df.columns else df.columns[0]
        records = []
        for _, row in df.iterrows():
            kat = row.get("kategori","Slow"); hpp = row.get("hpp",0.0)
            overall_rr = row.get("runrate_bulanan",0.0); n = max(len(stock_cols),1)
            for branch, scol in stock_cols.items():
                stok = row.get(scol, 0.0) if scol in row.index else 0.0
                if branch in sales_cols and sales_cols[branch] in row.index:
                    terjual = row.get(sales_cols[branch], 0.0)
                    rr = round(terjual / RUNRATE_HISTORY_MONTHS, 2)
                else:
                    terjual = 0.0; rr = round(overall_rr / n, 2)
                min_s = round(rr * _MULT.get(kat, 0.0))
                cov = safe_divide(stok, rr, 999.0 if stok>0 else 0.0)
                records.append({
                    "nama_barang": row.get(name_col,""), "kategori": kat, "hpp": hpp,
                    "branch": branch, "area": BRANCH_TO_AREA.get(branch,"Unknown"),
                    "stok_cabang": stok, "terjual_cabang": terjual, "runrate_cabang": rr,
                    "min_stock_cabang": min_s, "coverage_cabang": round(cov,2),
                    "stock_day_cabang": round(cov*30),
                })
        return pd.DataFrame(records)

    @staticmethod
    def _branch_status(long_df):
        if long_df.empty: long_df["status"] = []; return long_df
        df = long_df.copy()
        def _s(row):
            sd=row["stock_day_cabang"]; ms=row["min_stock_cabang"]; stok=row["stok_cabang"]
            if sd < CRITICAL_STOCK_DAY and ms > 0: return "Critical"
            if ms <= 0: return "Normal" if stok==0 else "Overstock"
            ratio = stok/ms
            return "Overstock" if ratio>OVERSTOCK_RATIO else "Understock" if ratio<UNDERSTOCK_RATIO else "Normal"
        df["status"] = df.apply(_s, axis=1); return df

    @staticmethod
    def _branch_summary(long_df):
        if long_df.empty: return pd.DataFrame()
        rows = []
        for branch, grp in long_df.groupby("branch"):
            grp = grp.copy(); grp["nilai_inv"] = grp["stok_cabang"] * grp["hpp"]
            dead = grp[grp["kategori"]=="Dead Stock"]
            sc = grp["status"].value_counts().to_dict() if "status" in grp.columns else {}
            rows.append({
                "branch":branch, "branch_name":BRANCH_FULL_NAMES.get(branch,branch),
                "area":BRANCH_TO_AREA.get(branch,"Unknown"),
                "total_sku":grp["nama_barang"].nunique(), "total_stok":grp["stok_cabang"].sum(),
                "total_terjual":grp["terjual_cabang"].sum(), "inventory_value":grp["nilai_inv"].sum(),
                "dead_stock_value":(dead["stok_cabang"]*dead["hpp"]).sum(),
                "fast_moving_sku":grp[grp["kategori"].isin(["Very Fast","Fast"])]["nama_barang"].nunique(),
                "dead_stock_sku":dead["nama_barang"].nunique(),
                "overstock_count":sc.get("Overstock",0), "normal_count":sc.get("Normal",0),
                "understock_count":sc.get("Understock",0), "critical_count":sc.get("Critical",0),
            })
        return pd.DataFrame(rows)

    @staticmethod
    def _health_scores(summary_df):
        if summary_df.empty: return summary_df
        def _score(row):
            total = max(row["total_sku"],1)
            fa = safe_divide(row["fast_moving_sku"],total)*100
            dr = safe_divide(row["dead_stock_sku"],total)*100
            or_ = safe_divide(row["overstock_count"],total)*100
            cr = safe_divide(row["critical_count"],total)*100
            ur = safe_divide(row["understock_count"],total)*100
            w = HEALTH_SCORE_WEIGHTS
            return round(max(0,min(100,
                fa*w.fast_moving_availability+(100-dr)*w.dead_stock_ratio+
                (100-cr)*w.inventory_turnover+(100-or_)*w.overstock_ratio+
                max(0,100-cr-ur)*w.service_level)),1)
        df = summary_df.copy()
        df["health_score"] = df.apply(_score, axis=1)
        df = df.sort_values("health_score",ascending=False).reset_index(drop=True)
        df["rank"] = df.index+1
        return df

    @staticmethod
    def _transfers(long_df):
        if long_df.empty:
            return pd.DataFrame(columns=["nama_barang","kategori","area","dari_cabang","ke_cabang","qty_transfer","hpp","nilai_transfer"])
        df = long_df.copy()
        df["surplus"] = (df["stok_cabang"]-df["min_stock_cabang"]).clip(lower=0)
        df["deficit"] = (df["min_stock_cabang"]-df["stok_cabang"]).clip(lower=0)
        records = []
        for (product, area), grp in df.groupby(["nama_barang","area"]):
            donors = grp[grp["surplus"]>0].sort_values("surplus",ascending=False)
            receivers = grp[grp["deficit"]>0].sort_values("deficit",ascending=False)
            if donors.empty or receivers.empty: continue
            pool = donors.set_index("branch")["surplus"].to_dict()
            kat = grp["kategori"].iloc[0]; hpp = grp["hpp"].iloc[0]
            for _, recv in receivers.iterrows():
                needed = recv["deficit"]
                for db in list(pool.keys()):
                    avail = pool[db]
                    if avail<=0 or needed<=0: continue
                    qty = min(needed, avail)
                    records.append({"nama_barang":product,"kategori":kat,"area":area,
                        "dari_cabang":db,"ke_cabang":recv["branch"],"qty_transfer":qty,"hpp":hpp,"nilai_transfer":qty*hpp})
                    pool[db] -= qty; needed -= qty
        return pd.DataFrame(records)

    @staticmethod
    def _dead_stock(df):
        dead = df[df["kategori"]=="Dead Stock"].copy()
        if dead.empty: return dead
        dead["dead_stock_value"] = dead["total_stok"] * dead["hpp"]
        def _age(row):
            rr=row["runrate_bulanan"]; stok=row["total_stok"]
            return round(stok/rr,1) if rr>0 else (99.0 if stok>0 else 0.0)
        dead["estimasi_bulan_tersimpan"] = dead.apply(_age, axis=1)
        def _action(m):
            for b in DEAD_STOCK_BUCKETS:
                if b.min_months<=m<b.max_months: return b.action, b.reason
            return "Monitor","Baru masuk dead stock, monitor 1-2 bulan."
        ar = dead["estimasi_bulan_tersimpan"].apply(_action)
        dead["rekomendasi_aksi"] = ar.apply(lambda x: x[0])
        dead["alasan"] = ar.apply(lambda x: x[1])
        return dead.sort_values("dead_stock_value",ascending=False).reset_index(drop=True)

    @staticmethod
    def _purchasing(df):
        df = df.copy()
        def _p(row):
            if row.get("kategori")=="Dead Stock" or row.get("margin_persen",0)<=0: return "Priority C"
            if (row.get("runrate_bulanan",0)>=PRIORITY_A_RUNRATE_MIN and
                    row.get("stock_day",999)<=PRIORITY_A_STOCKDAY_MAX and
                    row.get("margin_persen",0)>=PRIORITY_A_MARGIN_MIN): return "Priority A"
            return "Priority B"
        def _r(row):
            p=row.get("priority","B"); rr=row.get("runrate_bulanan",0); sd=row.get("stock_day",0); mg=row.get("margin_persen",0)
            if p=="Priority A": return f"Runrate {rr:.0f}/bulan, stok {sd:.0f} hari, margin {mg:.1f}%. Beli sekarang."
            if p=="Priority C":
                return f"Dead stock, stok {sd:.0f} hari. Jangan beli." if row.get("kategori")=="Dead Stock" else f"Margin tidak sehat ({mg:.1f}%)."
            return f"Stabil, monitor ({sd:.0f} hari)."
        df["priority"] = df.apply(_p, axis=1)
        df["alasan_purchasing"] = df.apply(_r, axis=1)
        return df

    @staticmethod
    def _revenue_summary(df, dead_df, transfer_df):
        inv_val = float(df.get("nilai_inventory", pd.Series(dtype=float)).sum())
        dead_val = float(dead_df["dead_stock_value"].sum()) if not dead_df.empty else 0.0
        restock_val = float(df.get("nilai_restock", pd.Series(dtype=float)).sum())
        transfer_val = float(transfer_df["nilai_transfer"].sum()) if not transfer_df.empty else 0.0
        profit = float(df.get("potensi_profit", pd.Series(dtype=float)).sum())
        revenue = float((df.get("harga_rekomendasi",pd.Series(dtype=float))*df.get("total_stok",pd.Series(dtype=float))).sum()) if "harga_rekomendasi" in df.columns else 0.0
        return {
            "inventory_value":inv_val,"dead_stock_value":dead_val,
            "dead_stock_pct":(dead_val/inv_val*100) if inv_val else 0.0,
            "transfer_value":transfer_val,"restock_value":restock_val,
            "potential_profit":profit,"potential_revenue":revenue,
            "total_sku":len(df),
            "fast_sku":int(df["kategori"].isin(["Very Fast","Fast"]).sum()) if "kategori" in df.columns else 0,
            "dead_sku":int((df["kategori"]=="Dead Stock").sum()) if "kategori" in df.columns else 0,
        }

    @staticmethod
    def _recommendations(df, dead_df, transfer_df, purchasing_df, branch_summary, revenue):
        recs = []
        name_col = "nama_barang" if "nama_barang" in df.columns else df.columns[0]
        if "priority" in purchasing_df.columns:
            pa = purchasing_df[purchasing_df["priority"]=="Priority A"].nlargest(4,"nilai_restock") if "nilai_restock" in purchasing_df.columns else purchasing_df[purchasing_df["priority"]=="Priority A"].head(4)
            for _,r in pa.iterrows():
                recs.append({"category":"Purchasing","priority":"Tinggi","icon":"🛒","text":f"Tambah pembelian {r[name_col]} — stok {r.get('stock_day',0):.0f} hari, runrate {r.get('runrate_bulanan',0):.0f}/bulan, margin {r.get('margin_persen',0):.1f}%."})
            pc = purchasing_df[(purchasing_df["priority"]=="Priority C")&(purchasing_df["kategori"]=="Dead Stock")]
            for _,r in pc.head(3).iterrows():
                recs.append({"category":"Purchasing","priority":"Tinggi","icon":"🚫","text":f"Jangan beli {r[name_col]} — dead stock, coverage {r.get('coverage_month',0):.0f} bulan."})
        for _,r in (transfer_df.nlargest(4,"nilai_transfer").iterrows() if not transfer_df.empty else []):
            recs.append({"category":"Transfer","priority":"Sedang","icon":"🔄","text":f"Transfer {r['qty_transfer']:.0f} unit {r['nama_barang']} dari {r['dari_cabang']} → {r['ke_cabang']} ({r['area']}), hemat {format_rupiah_short(r['nilai_transfer'])}."})
        for _,r in df[df["kategori"]=="Very Fast"].nlargest(3,"runrate_bulanan").iterrows():
            recs.append({"category":"Pricing","priority":"Sedang","icon":"📈","text":f"Naikkan {r[name_col]} ke H2 — permintaan {r['runrate_bulanan']:.0f}/bulan."})
        for _,r in df[df["kategori"]=="Slow"].nlargest(3,"total_stok").iterrows():
            recs.append({"category":"Pricing","priority":"Sedang","icon":"📉","text":f"Turunkan {r[name_col]} ke HD — stok {r['total_stok']:.0f} unit, pergerakan lambat."})
        if not dead_df.empty:
            for action,icon in [("Clearance","🚨"),("Bundling","📦"),("Turunkan ke HD","🔽")]:
                for _,r in dead_df[dead_df["rekomendasi_aksi"]==action].head(2).iterrows():
                    recs.append({"category":"Dead Stock","priority":"Tinggi" if action=="Clearance" else "Sedang","icon":icon,
                                 "text":f"{action}: {r[name_col]} — {r['estimasi_bulan_tersimpan']:.0f} bulan, modal {format_rupiah_short(r['dead_stock_value'])}."})
        if not branch_summary.empty:
            worst=branch_summary.iloc[-1]; best=branch_summary.iloc[0]
            recs.append({"category":"Branch","priority":"Tinggi","icon":"⚠️","text":f"Cabang {worst['branch_name']} ({worst['branch']}) Health Score terendah ({worst['health_score']:.0f}/100)."})
            recs.append({"category":"Branch","priority":"Rendah","icon":"✅","text":f"Cabang {best['branch_name']} paling sehat ({best['health_score']:.0f}/100), jadikan best practice."})
            over=branch_summary[branch_summary["overstock_count"]>0].nlargest(1,"overstock_count")
            if not over.empty:
                r=over.iloc[0]; recs.append({"category":"Branch","priority":"Sedang","icon":"📦","text":f"Cabang {r['branch_name']} overstock {r['overstock_count']:.0f} SKU — transfer ke {r['area']}."})
            crit=branch_summary[branch_summary["critical_count"]>0].nlargest(1,"critical_count")
            if not crit.empty:
                r=crit.iloc[0]; recs.append({"category":"Branch","priority":"Tinggi","icon":"🔴","text":f"Cabang {r['branch_name']} ada {r['critical_count']:.0f} SKU Critical — stok habis dalam <30 hari."})
        dp=revenue.get("dead_stock_pct",0)
        if dp>30: recs.append({"category":"Revenue","priority":"Tinggi","icon":"🔴","text":f"Dead stock {dp:.1f}% ({format_rupiah_short(revenue.get('dead_stock_value',0))}) — kondisi kritis."})
        elif dp>15: recs.append({"category":"Revenue","priority":"Sedang","icon":"🟡","text":f"Dead stock {dp:.1f}% — waspadai tren kenaikan."})
        if revenue.get("transfer_value",0)>0:
            recs.append({"category":"Revenue","priority":"Sedang","icon":"💡","text":f"Optimalkan transfer {format_rupiah_short(revenue['transfer_value'])} sebelum PO baru."})
        while len(recs)<15:
            for _,r in df.sort_values("runrate_bulanan",ascending=False).head(15-len(recs)).iterrows():
                recs.append({"category":"Inventory","priority":"Rendah","icon":"📋","text":f"Pantau {r[name_col]} — {r.get('kategori','')} runrate {r.get('runrate_bulanan',0):.1f}/bulan."})
            break
        return recs
