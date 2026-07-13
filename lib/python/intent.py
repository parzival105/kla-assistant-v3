"""
modules/sales_assistant/intent.py
===================================
Intent Detection Engine — menganalisa input natural language dari sales
dan menentukan engine mana yang harus dipanggil:
  - PRODUCT_SEARCH   : cari produk spesifik (monitor, mouse, printer, dll)
  - PC_BUILDER       : rakit PC / build spec (customer minta PC gaming, editing, dll)
  - COMPATIBILITY    : upgrade / cek kompatibilitas (RAM laptop, tinta printer, dll)
  - STOCK_CHECK      : cek ketersediaan stok produk tertentu
  - GENERAL          : pertanyaan umum / tidak spesifik
"""
from __future__ import annotations
import json, logging, re
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# Intent categories
INTENT_PRODUCT_SEARCH  = "PRODUCT_SEARCH"
INTENT_PC_BUILDER      = "PC_BUILDER"
INTENT_COMPATIBILITY   = "COMPATIBILITY"
INTENT_STOCK_CHECK     = "STOCK_CHECK"
INTENT_GENERAL         = "GENERAL"

# Keywords untuk rule-based fallback
_PC_BUILDER_KEYWORDS = [
    "rakit", "rakitan", "build", "pc gaming", "pc editing", "pc kantor",
    "pc design", "pc render", "komputer gaming", "komputer editing",
    "bikin pc", "buat pc", "pc workstation", "pc coding", "pc office",
    "bangun pc", "konfigurasi pc", "spek pc",
]

_COMPATIBILITY_KEYWORDS = [
    "upgrade", "cocok", "compatible", "kompatibel", "support",
    "bisa dipasang", "tinta", "cartridge", "refill", "ink",
    "baterai", "charger", "adaptor", "kabel", "sparepart",
    "bisa diupgrade", "slot", "socket", "ddr", "bisa pakai",
]

_STOCK_KEYWORDS = [
    "stok", "stock", "ada gak", "ada tidak", "tersedia", "ready",
    "kosong", "habis", "cabang mana", "dimana ada", "ketersediaan",
]

_PRODUCT_CATEGORIES = [
    "laptop", "monitor", "keyboard", "mouse", "headset", "webcam",
    "flashdisk", "ssd", "ram", "vga", "gpu", "router", "printer",
    "access point", "cctv", "ups", "microphone", "kursi", "chair",
    "gadget", "hp", "handphone", "tablet", "speaker", "modem",
    "switch", "hub", "kabel", "cable", "cooling", "fan", "cooler",
    "casing", "power supply", "psu", "motherboard", "processor",
    "cpu", "hardisk", "hdd", "optical drive", "dvd", "bluray",
    "projector", "scanner", "external", "docking", "adapter",
    "tinta", "kertas", "cartridge", "toner",
]


@dataclass
class IntentResult:
    intent: str
    confidence: float          # 0.0 – 1.0
    extracted_query: str       # cleaned query for downstream engines
    category_hint: str         # e.g. "monitor", "printer", "RAM"
    budget_hint: Optional[float] = None
    brand_hint: Optional[str]  = None
    use_case_hint: Optional[str] = None  # "gaming", "kantor", "editing"


def detect_intent(user_input: str) -> IntentResult:
    """
    Detect sales intent from natural language input.
    Uses Claude AI for primary detection with rule-based fallback.
    """
    # Try Claude AI first
    ai_result = _detect_via_ai(user_input)
    if ai_result and ai_result.confidence >= 0.7:
        return ai_result

    # Fallback: rule-based
    return _detect_rule_based(user_input)


def _detect_via_ai(user_input: str) -> Optional[IntentResult]:
    """Use Claude API to detect intent and extract entities."""
    try:
        import requests
        prompt = f"""Kamu adalah intent detection engine untuk toko komputer KLA.
Analisa input sales berikut dan tentukan intent-nya.

Input: "{user_input}"

Kembalikan HANYA JSON valid (tanpa markdown, tanpa penjelasan):
{{
  "intent": "PRODUCT_SEARCH" | "PC_BUILDER" | "COMPATIBILITY" | "STOCK_CHECK" | "GENERAL",
  "confidence": 0.0-1.0,
  "extracted_query": "query bersih untuk pencarian",
  "category_hint": "kategori produk utama (monitor/laptop/printer/RAM/dll) atau kosong",
  "budget_hint": angka_rupiah_atau_null,
  "brand_hint": "nama brand atau null",
  "use_case_hint": "gaming/kantor/editing/usaha/dll atau null"
}}

Aturan intent:
- PRODUCT_SEARCH: customer cari produk spesifik (monitor, mouse, printer, headset, dll)
- PC_BUILDER: customer minta dirakit/dibangun PC (PC gaming, PC editing, rakit komputer)
- COMPATIBILITY: upgrade, cek cocok/tidak, tinta printer, aksesori spesifik untuk device tertentu
- STOCK_CHECK: tanya ketersediaan stok di cabang tertentu
- GENERAL: pertanyaan umum, garansi, service, dll"""

        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"Content-Type": "application/json"},
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 300,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=10,
        )
        data = resp.json()
        text = "".join(b["text"] for b in data.get("content", []) if b.get("type") == "text")
        text = text.strip().replace("```json", "").replace("```", "").strip()
        parsed = json.loads(text)

        budget = parsed.get("budget_hint")
        if isinstance(budget, str):
            budget = _parse_budget(budget)

        return IntentResult(
            intent=parsed.get("intent", INTENT_GENERAL),
            confidence=float(parsed.get("confidence", 0.5)),
            extracted_query=parsed.get("extracted_query", user_input),
            category_hint=parsed.get("category_hint", ""),
            budget_hint=budget,
            brand_hint=parsed.get("brand_hint"),
            use_case_hint=parsed.get("use_case_hint"),
        )
    except Exception as e:
        logger.warning(f"AI intent detection failed: {e}")
        return None


def _detect_rule_based(user_input: str) -> IntentResult:
    """Rule-based fallback intent detection."""
    text = user_input.lower().strip()

    # PC Builder check
    if any(kw in text for kw in _PC_BUILDER_KEYWORDS):
        return IntentResult(
            intent=INTENT_PC_BUILDER, confidence=0.85,
            extracted_query=user_input, category_hint="PC Rakitan",
            budget_hint=_parse_budget(text),
            use_case_hint=_extract_use_case(text),
        )

    # Compatibility check
    if any(kw in text for kw in _COMPATIBILITY_KEYWORDS):
        return IntentResult(
            intent=INTENT_COMPATIBILITY, confidence=0.80,
            extracted_query=user_input, category_hint=_extract_category(text),
            brand_hint=_extract_brand_hint(text),
        )

    # Stock check
    if any(kw in text for kw in _STOCK_KEYWORDS):
        return IntentResult(
            intent=INTENT_STOCK_CHECK, confidence=0.80,
            extracted_query=user_input, category_hint=_extract_category(text),
        )

    # Product search (default if category keyword found)
    cat = _extract_category(text)
    if cat:
        return IntentResult(
            intent=INTENT_PRODUCT_SEARCH, confidence=0.75,
            extracted_query=user_input, category_hint=cat,
            budget_hint=_parse_budget(text),
            brand_hint=_extract_brand_hint(text),
            use_case_hint=_extract_use_case(text),
        )

    return IntentResult(
        intent=INTENT_GENERAL, confidence=0.5,
        extracted_query=user_input, category_hint="",
    )


def _parse_budget(text: str) -> Optional[float]:
    """Extract budget amount from text."""
    text = text.lower().replace(".", "").replace(",", "")
    # Pattern: angka + juta/jt/ribu/rb/k
    m = re.search(r"(\d+(?:\.\d+)?)\s*(juta|jt|million)", text)
    if m: return float(m.group(1)) * 1_000_000
    m = re.search(r"(\d+(?:\.\d+)?)\s*(ribu|rb|k\b)", text)
    if m: return float(m.group(1)) * 1_000
    # Plain number > 100000 assumed rupiah
    m = re.search(r"\b(\d{6,})\b", text)
    if m: return float(m.group(1))
    return None


def _extract_category(text: str) -> str:
    """Extract product category hint from text."""
    for cat in _PRODUCT_CATEGORIES:
        if cat in text:
            return cat.title()
    return ""


def _extract_brand_hint(text: str) -> Optional[str]:
    """Extract brand name hint."""
    brands = ["logitech","asus","acer","hp","dell","lenovo","samsung","lg","aoc","benq",
              "msi","gigabyte","asrock","intel","amd","nvidia","sandisk","kingston",
              "lexar","adata","teamgroup","corsair","epson","canon","brother","tp-link",
              "tplink","ubiquiti","hikvision","dahua","viewsonic","xiaomi","realme",
              "rexus","fantech","hyperx","steelseries","razer","cooler master","noctua",
              "deepcool","seasonic","corsair","be quiet","evga"]
    tl = text.lower()
    for b in brands:
        if b in tl:
            return b.title().replace("Tp-Link", "TP-Link")
    return None


def _extract_use_case(text: str) -> Optional[str]:
    """Extract use case hint."""
    cases = {
        "gaming": ["gaming","game","gamer","fps","moba","esport"],
        "editing": ["editing","edit","video","youtube","content creator","render","desain","design","grafis"],
        "kantor": ["kantor","office","kerja","work","bisnis","business","presentasi"],
        "coding": ["coding","code","programmer","developer","programming"],
        "usaha": ["usaha","toko","warnet","cafe","bisnis"],
    }
    tl = text.lower()
    for case, keywords in cases.items():
        if any(kw in tl for kw in keywords):
            return case
    return None
