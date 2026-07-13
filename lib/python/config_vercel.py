"""config_vercel.py — Config for Vercel serverless functions."""
from __future__ import annotations
from dataclasses import dataclass

APP_NAME     = "KLA Business Suite"
APP_VERSION  = "1.0"
COMPANY_NAME = "PT KLA Teknologi Indonesia"
TAGLINE      = "Komplit · Nyaman · Bergaransi"

ROLE_SUPER_ADMIN  = "super_admin"
ROLE_AREA_MANAGER = "area_manager"
ROLE_STORE_LEADER = "store_leader"
ROLE_SALES        = "sales"
ROLE_LABELS = {"super_admin":"Super Admin","area_manager":"Area Manager","store_leader":"Store Leader","sales":"Sales"}
ROLE_COLORS = {"super_admin":"#a855f7","area_manager":"#3b82f6","store_leader":"#10b981","sales":"#f59e0b"}

ALL_BRANCHES = ["SMG","YK","SLA","TGL","PKL","CRB","KDR","NGL","SKH","MSBY","MJK","BSBY","PWT"]
EXCLUDED_BRANCH_COLS = ["HO","SOLO","TSM"]
AREA_MAP = {
    "Area 1 — Jawa Tengah Barat": ["CRB","PWT","SLA","TGL","PKL"],
    "Area 2 — Jawa Tengah Timur": ["SMG","NGL","YK","SKH"],
    "Area 3 — Jawa Timur":        ["KDR","MJK","MSBY","BSBY"],
}
BRANCH_TO_AREA = {b: a for a, bs in AREA_MAP.items() for b in bs}
BRANCH_FULL_NAMES = {
    "SMG":"Semarang","YK":"Yogyakarta","SLA":"Slawi","TGL":"Tegal","PKL":"Pekalongan",
    "CRB":"Cirebon","KDR":"Kediri","NGL":"Ngaliyan","SKH":"Sukoharjo",
    "MSBY":"Surabaya Merr","MJK":"Mojokerto","BSBY":"Surabaya Babatan","PWT":"Purwokerto",
}

@dataclass(frozen=True)
class CategoryThreshold:
    name:str; min_runrate:float; max_runrate:float; min_stock_multiplier:float

CATEGORY_THRESHOLDS = [
    CategoryThreshold("Very Fast",25.0,float("inf"),2.0),
    CategoryThreshold("Fast",15.0,25.0,1.5),
    CategoryThreshold("Slow",4.0,15.0,1.0),
    CategoryThreshold("Dead Stock",0.0,4.0,0.0),
]
CATEGORY_COLORS = {"Very Fast":"#059669","Fast":"#7c3aed","Slow":"#d97706","Dead Stock":"#dc2626"}

RUNRATE_HISTORY_MONTHS  = 6
OVERSTOCK_RATIO         = 1.50
UNDERSTOCK_RATIO        = 0.80
CRITICAL_STOCK_DAY      = 30
PRIORITY_A_RUNRATE_MIN  = 15.0
PRIORITY_A_STOCKDAY_MAX = 30.0
PRIORITY_A_MARGIN_MIN   = 10.0

EXCLUDED_KEYWORDS = ["laptop","notebook","pc","aio","tablet","display","bonus","cabutan","service","jasa"]

@dataclass(frozen=True)
class DeadStockBucket:
    min_months:float; max_months:float; action:str; reason:str

DEAD_STOCK_BUCKETS = [
    DeadStockBucket(3,6,"Turunkan ke HD","Stok 3-6 bulan."),
    DeadStockBucket(6,12,"Bundling","Stok 6-12 bulan."),
    DeadStockBucket(12,float("inf"),"Clearance","Stok >12 bulan."),
]
PRICING_TIER_MAP = {"Very Fast":"h2","Fast":"h1","Slow":"hd","Dead Stock":"hd"}

@dataclass(frozen=True)
class HealthScoreWeights:
    fast_moving_availability:float=0.25
    dead_stock_ratio:float=0.25
    inventory_turnover:float=0.20
    overstock_ratio:float=0.15
    service_level:float=0.15

HEALTH_SCORE_WEIGHTS = HealthScoreWeights()

PC_COMPONENT_CATEGORIES = {
    "PROCESSOR":"Processor","MOTHERBOARD":"Motherboard",
    "RAM SODIMM":"RAM (Laptop)","RAM LONGDIMM":"RAM (Desktop)",
    "SSD INTERNAL":"SSD","HDD INTERNAL":"HDD","GRAPHIC CARD":"Graphic Card",
    "CASING PC":"Casing","POWER SUPPLY":"Power Supply","INTERNAL COOLER":"CPU Cooler",
}
PC_BUILD_TYPES = [
    "Office / Kerja","Gaming Entry","Gaming Mid-range","Gaming High-end",
    "Desain Grafis","Video Editing","Coding / Development","Workstation","HTPC / Media Center",
]
PC_BUDGET_TIERS = [
    {"label":"Entry (Rp 3-5 juta)","min":3_000_000,"max":5_000_000},
    {"label":"Mid-Low (Rp 5-8 juta)","min":5_000_000,"max":8_000_000},
    {"label":"Mid (Rp 8-12 juta)","min":8_000_000,"max":12_000_000},
    {"label":"Mid-High (Rp 12-18 juta)","min":12_000_000,"max":18_000_000},
    {"label":"High (Rp 18-25 juta)","min":18_000_000,"max":25_000_000},
    {"label":"Premium (Rp 25-35 juta)","min":25_000_000,"max":35_000_000},
]
COLUMN_ALIASES = {
    "nama_barang":     ["nama barang","nama_barang","product name","item","barang"],
    "kategori_produk": ["kategori barang","kategori","category","jenis barang"],
    "segment":         ["segment","segmen","tipe"],
    "brand":           ["merek","brand","merk"],
    "hpp":             ["hpp","harga pokok","cost","modal"],
    "hd":              ["hd","h.d.","harga dasar"],
    "h1":              ["h1","harga 1"],
    "h2":              ["h2","harga 2"],
    "total_stok":      ["total stoks","total stok","total stock","stok total"],
    "total_terjual":   ["total terjual","total sold","terjual"],
}

@dataclass(frozen=True)
class Theme:
    bg_primary:str="#0d0516"; bg_card:str="#180d28"; border:str="#2d1a45"
    text_primary:str="#e2e8f0"; brand:str="#431061"; accent:str="#a855f7"

THEME = Theme()
