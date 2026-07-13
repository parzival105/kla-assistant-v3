"""lib/python/pc_builder.py — PC Build Engine using local blob store components."""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Optional
from lib.python.config_vercel import PC_COMPONENT_CATEGORIES, BRANCH_FULL_NAMES
from lib.python.compatibility import check_compatibility
from lib.python.storage import load_components_json
from lib.python.helper import normalize_text

logger = logging.getLogger(__name__)

@dataclass
class BuildComponent:
    kategori:str; kategori_label:str; nama:str; brand:str
    hpp:float; h1:float; h2:float; selling_price:float; stok:int
    branch_stock:dict = field(default_factory=dict)

    def branch_stock_text(self) -> str:
        if not self.branch_stock: return "—"
        return " · ".join([f"{BRANCH_FULL_NAMES.get(b,b)}: {q}" for b,q in sorted(self.branch_stock.items(), key=lambda x:-x[1])])

@dataclass
class BuildResult:
    build_type:str; budget:float; total_hpp:float; total_price:float
    margin_nominal:float; margin_persen:float
    components:list = field(default_factory=list)
    compatibility_notes:list = field(default_factory=list)
    compatibility_warnings:list = field(default_factory=list)
    build_warnings:list = field(default_factory=list)
    is_within_budget:bool = True
    ai_explanation:str = ""

BUILD_PROFILES = {
    "Office / Kerja":       {"needs_gpu":False,"alloc":{"PROCESSOR":.30,"MOTHERBOARD":.20,"RAM LONGDIMM":.15,"SSD INTERNAL":.13,"CASING PC":.10,"POWER SUPPLY":.09,"INTERNAL COOLER":.03}},
    "Gaming Entry":         {"needs_gpu":True, "alloc":{"PROCESSOR":.18,"MOTHERBOARD":.15,"RAM LONGDIMM":.10,"SSD INTERNAL":.10,"GRAPHIC CARD":.28,"CASING PC":.08,"POWER SUPPLY":.08,"INTERNAL COOLER":.03}},
    "Gaming Mid-range":     {"needs_gpu":True, "alloc":{"PROCESSOR":.17,"MOTHERBOARD":.14,"RAM LONGDIMM":.10,"SSD INTERNAL":.09,"GRAPHIC CARD":.32,"CASING PC":.08,"POWER SUPPLY":.07,"INTERNAL COOLER":.03}},
    "Gaming High-end":      {"needs_gpu":True, "alloc":{"PROCESSOR":.16,"MOTHERBOARD":.13,"RAM LONGDIMM":.10,"SSD INTERNAL":.08,"GRAPHIC CARD":.37,"CASING PC":.07,"POWER SUPPLY":.06,"INTERNAL COOLER":.03}},
    "Desain Grafis":        {"needs_gpu":True, "alloc":{"PROCESSOR":.22,"MOTHERBOARD":.14,"RAM LONGDIMM":.13,"SSD INTERNAL":.10,"GRAPHIC CARD":.25,"CASING PC":.07,"POWER SUPPLY":.06,"INTERNAL COOLER":.03}},
    "Video Editing":        {"needs_gpu":True, "alloc":{"PROCESSOR":.24,"MOTHERBOARD":.13,"RAM LONGDIMM":.15,"SSD INTERNAL":.12,"GRAPHIC CARD":.22,"CASING PC":.07,"POWER SUPPLY":.05,"INTERNAL COOLER":.02}},
    "Coding / Development": {"needs_gpu":False,"alloc":{"PROCESSOR":.28,"MOTHERBOARD":.18,"RAM LONGDIMM":.18,"SSD INTERNAL":.14,"CASING PC":.10,"POWER SUPPLY":.09,"INTERNAL COOLER":.03}},
    "Workstation":          {"needs_gpu":True, "alloc":{"PROCESSOR":.25,"MOTHERBOARD":.15,"RAM LONGDIMM":.18,"SSD INTERNAL":.10,"GRAPHIC CARD":.20,"CASING PC":.06,"POWER SUPPLY":.05,"INTERNAL COOLER":.01}},
    "HTPC / Media Center":  {"needs_gpu":False,"alloc":{"PROCESSOR":.30,"MOTHERBOARD":.22,"RAM LONGDIMM":.15,"SSD INTERNAL":.15,"CASING PC":.12,"POWER SUPPLY":.06}},
}
BUILD_PRIORITY = {
    "Office / Kerja":       ["PROCESSOR","MOTHERBOARD","RAM LONGDIMM","SSD INTERNAL","CASING PC","POWER SUPPLY","INTERNAL COOLER"],
    "Gaming Entry":         ["GRAPHIC CARD","PROCESSOR","RAM LONGDIMM","SSD INTERNAL","MOTHERBOARD","POWER SUPPLY","CASING PC","INTERNAL COOLER"],
    "Gaming Mid-range":     ["GRAPHIC CARD","PROCESSOR","RAM LONGDIMM","SSD INTERNAL","MOTHERBOARD","POWER SUPPLY","CASING PC","INTERNAL COOLER"],
    "Gaming High-end":      ["GRAPHIC CARD","PROCESSOR","RAM LONGDIMM","MOTHERBOARD","SSD INTERNAL","POWER SUPPLY","CASING PC","INTERNAL COOLER"],
    "Desain Grafis":        ["PROCESSOR","RAM LONGDIMM","GRAPHIC CARD","SSD INTERNAL","MOTHERBOARD","POWER SUPPLY","CASING PC","INTERNAL COOLER"],
    "Video Editing":        ["PROCESSOR","RAM LONGDIMM","SSD INTERNAL","GRAPHIC CARD","MOTHERBOARD","POWER SUPPLY","CASING PC","INTERNAL COOLER"],
    "Coding / Development": ["PROCESSOR","RAM LONGDIMM","SSD INTERNAL","MOTHERBOARD","CASING PC","POWER SUPPLY","INTERNAL COOLER"],
    "Workstation":          ["PROCESSOR","RAM LONGDIMM","MOTHERBOARD","GRAPHIC CARD","SSD INTERNAL","POWER SUPPLY","CASING PC","INTERNAL COOLER"],
    "HTPC / Media Center":  ["PROCESSOR","SSD INTERNAL","RAM LONGDIMM","MOTHERBOARD","CASING PC","POWER SUPPLY"],
}

class PCBuildEngine:
    def __init__(self):
        # Load components once from local blob store
        self._components = load_components_json()

    def _get_by_category(self, category: str) -> list:
        return [c for c in self._components if c.get("kategori","").upper() == category.upper() and c.get("is_available",True) and c.get("h1",0) > 0]

    def build(self, build_type:str, budget:float, preferred_brand:Optional[str]=None) -> Optional[BuildResult]:
        profile = BUILD_PROFILES.get(build_type)
        if not profile: return None
        alloc     = profile["alloc"]
        priority  = BUILD_PRIORITY.get(build_type, list(alloc.keys()))
        needs_gpu = profile["needs_gpu"]
        selected:dict = {}; remaining=budget; warnings=[]

        for cat in priority:
            if cat not in alloc: continue
            if cat == "GRAPHIC CARD" and not needs_gpu: continue
            comp = self._select(cat, budget*alloc[cat], remaining, preferred_brand if cat=="PROCESSOR" else None)
            if comp: selected[cat]=comp; remaining-=comp.selling_price
            else: warnings.append(f"Tidak ada '{PC_COMPONENT_CATEGORIES.get(cat,cat)}' tersedia di budget ini.")

        if not selected: return None

        cpu_n = selected.get("PROCESSOR",""); mb_n = selected.get("MOTHERBOARD","")
        ram_n = selected.get("RAM LONGDIMM",selected.get("RAM SODIMM",""))
        gpu_n = selected.get("GRAPHIC CARD",""); psu_n = selected.get("POWER SUPPLY","")
        compat = check_compatibility(
            cpu_name=cpu_n.nama if isinstance(cpu_n,BuildComponent) else "",
            mb_name=mb_n.nama   if isinstance(mb_n,BuildComponent) else "",
            ram_name=ram_n.nama if isinstance(ram_n,BuildComponent) else "",
            gpu_name=gpu_n.nama if isinstance(gpu_n,BuildComponent) else "",
            psu_name=psu_n.nama if isinstance(psu_n,BuildComponent) else "",
        )

        total_hpp   = sum(c.hpp for c in selected.values())
        total_price = sum(c.selling_price for c in selected.values())
        margin_nom  = total_price - total_hpp
        margin_pct  = (margin_nom/total_price*100) if total_price>0 else 0.0

        return BuildResult(
            build_type=build_type, budget=budget, total_hpp=total_hpp,
            total_price=total_price, margin_nominal=margin_nom, margin_persen=margin_pct,
            components=list(selected.values()), compatibility_notes=compat.notes,
            compatibility_warnings=compat.warnings, build_warnings=warnings,
            is_within_budget=total_price<=budget*1.05,
        )

    def _select(self, category, target, remaining, preferred_brand=None):
        comps = self._get_by_category(category)
        if not comps: return None
        affordable = [c for c in comps if c["h1"]<=remaining]
        if not affordable: return None
        if preferred_brand:
            bm=[c for c in affordable if preferred_brand.lower() in normalize_text(c["nama_barang"])]
            if bm: affordable=bm
        within = [c for c in affordable if c["h1"]<=target]
        best = max(within,key=lambda c:c["h1"]) if within else min(affordable,key=lambda c:c["h1"])
        return BuildComponent(
            kategori=category, kategori_label=PC_COMPONENT_CATEGORIES.get(category,category),
            nama=best["nama_barang"], brand=best.get("brand",""),
            hpp=float(best.get("hpp",0)), h1=float(best["h1"]), h2=float(best.get("h2",0)),
            selling_price=float(best["h1"]), stok=int(best.get("total_stok",0)),
            branch_stock=best.get("branch_stock",{}),
        )

    def generate_alternatives(self, build_type, budget, n=2):
        return [alt for factor in [0.85,1.15][:n] if (alt:=self.build(build_type,budget*factor))]

def load_components_from_stock(stock_df, branch_cols:dict) -> tuple[int, list]:
    """Extract PC components from stock DataFrame, return (count, components_list)."""
    import json
    from lib.python.helper import safe_numeric
    components = []
    cat_col = next((col for col in stock_df.columns if any(alias in str(col).lower() for alias in ["kategori barang","kategori","category"])), None)
    if not cat_col: return 0, []

    for pc_cat in PC_COMPONENT_CATEGORIES:
        subset = stock_df[stock_df[cat_col].astype(str).str.upper().str.strip()==pc_cat.upper()].copy()
        for _,row in subset.iterrows():
            nama = str(row.get("Nama Barang",row.get("nama_barang",""))).strip()
            if not nama: continue
            hpp  = float(safe_numeric(import_series([row.get("HPP",row.get("hpp",0))])))
            hd   = float(safe_numeric(import_series([row.get("HD", row.get("hd",0))])))
            h1   = float(safe_numeric(import_series([row.get("H1", row.get("h1",0))])))
            h2   = float(safe_numeric(import_series([row.get("H2", row.get("h2",0))])))
            stok = float(safe_numeric(import_series([row.get("Total Stoks",row.get("total_stok",0))])))
            branch_stock = {}
            for br, col in branch_cols.items():
                qty = int(float(row.get(col,0) or 0))
                if qty > 0: branch_stock[br] = qty
            components.append({
                "nama_barang":nama,"kategori":pc_cat,"segment":str(row.get("Segment",row.get("segment",""))or""),
                "brand":str(row.get("Merek",row.get("brand",""))or""),
                "hpp":hpp,"hd":hd,"h1":h1,"h2":h2,"total_stok":int(stok),
                "branch_stock":branch_stock,"is_available":stok>0,
            })
    return len(components), components

def import_series(val):
    import pandas as pd
    return pd.Series(val)
