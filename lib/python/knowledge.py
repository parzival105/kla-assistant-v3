"""
modules/sales_assistant/knowledge.py
======================================
Product Knowledge Engine — handles compatibility queries, upgrade advice,
and upsell suggestions using Claude AI + stock data.

Examples:
  "RAM laptop ASUS A14 bisa diupgrade?"
  → Find compatible RAM in stock, show options

  "Tinta Epson L3250"
  → Find compatible ink cartridges, suggest paper & maintenance

  "Upgrade SSD laptop gaming"
  → Suggest NVMe/SATA SSDs available in stock
"""
from __future__ import annotations
import json, logging
from dataclasses import dataclass, field
from typing import Optional
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeResult:
    query: str
    answer: str                    # AI-generated explanation
    recommended_products: list[dict] = field(default_factory=list)
    upsell_suggestions: list[dict]  = field(default_factory=list)
    compatibility_notes: list[str]  = field(default_factory=list)


class ProductKnowledgeEngine:
    """
    Combines Claude AI knowledge with real stock data to answer
    compatibility and upgrade queries.
    """

    def answer(
        self,
        query: str,
        df: pd.DataFrame,
        stock_columns: dict[str, str],
        role: str,
        category_hint: str = "",
    ) -> KnowledgeResult:
        """
        Answer a compatibility/upgrade query.

        Args:
            query: Natural language query from sales.
            df: Full enriched inventory DataFrame.
            stock_columns: branch_code -> column_name.
            role: User role for price visibility.
            category_hint: Category extracted by intent engine.

        Returns:
            KnowledgeResult with AI answer + product suggestions.
        """
        # Find relevant products from stock
        relevant = self._find_relevant_products(query, df, category_hint)

        # Build stock context for AI (NO HPP for AI prompt — security)
        stock_context = self._build_stock_context(relevant, stock_columns)

        # Call Claude AI for knowledge answer
        answer = self._get_ai_answer(query, stock_context)

        # Extract upsell opportunities
        upsell = self._find_upsell(query, df, category_hint)

        return KnowledgeResult(
            query=query,
            answer=answer,
            recommended_products=relevant[:5],
            upsell_suggestions=upsell[:3],
            compatibility_notes=self._extract_compat_notes(answer),
        )

    @staticmethod
    def _find_relevant_products(
        query: str, df: pd.DataFrame, category_hint: str
    ) -> list[dict]:
        """Find products in stock relevant to the query."""
        import re
        query_lower = query.lower()
        cat_lower   = category_hint.lower()

        searchable_cols = ["nama_barang", "segment", "brand"]
        tokens = [t for t in re.sub(r"[^a-z0-9\s]","", query_lower).split() if len(t) >= 2]

        results = []
        for _, row in df.iterrows():
            text = " ".join(str(row.get(c,"")) for c in searchable_cols).lower()
            score = sum(1 for t in tokens if t in text)
            if cat_lower and cat_lower in text:
                score += 2
            if score > 0 and row.get("total_stok", 0) > 0:
                results.append({
                    "nama": str(row.get("nama_barang","")),
                    "segment": str(row.get("segment","")),
                    "h1": float(row.get("h1", row.get("harga_rekomendasi", 0))),
                    "stok": int(row.get("total_stok", 0)),
                    "runrate": float(row.get("runrate_bulanan", 0)),
                    "score": score,
                })

        results.sort(key=lambda x: (-x["score"], -x["runrate"]))
        return results

    @staticmethod
    def _build_stock_context(products: list[dict], stock_columns: dict) -> str:
        """Build concise stock summary for AI prompt — NO HPP/margin."""
        if not products:
            return "Tidak ada produk relevan ditemukan di stok KLA saat ini."
        lines = ["Produk tersedia di stok KLA:"]
        for p in products[:8]:
            from lib.python.formatter import format_rupiah
            lines.append(f"- {p['nama']} | Harga: {format_rupiah(p['h1'])} | Stok: {p['stok']} unit | Laku: {p['runrate']:.1f}/bulan")
        return "\n".join(lines)

    @staticmethod
    def _get_ai_answer(query: str, stock_context: str) -> str:
        """Call Claude API for product knowledge answer."""
        try:
            import requests
            from lib.python.formatter import format_rupiah

            prompt = f"""Kamu adalah Product Knowledge Specialist di toko komputer KLA.
Sales sedang melayani customer dan butuh bantuan menjawab pertanyaan ini.

PERTANYAAN CUSTOMER: "{query}"

DATA STOK KLA SAAT INI:
{stock_context}

Jawab dengan:
1. Jawaban langsung dan jelas untuk customer
2. Rekomendasi produk spesifik dari stok KLA yang relevan
3. Tips atau saran tambahan jika ada (upsell yang natural, bukan memaksa)
4. Jika tentang kompatibilitas (upgrade RAM, tinta, dll) — jelaskan cara cek kompatibilitas

Format jawaban:
- Gunakan bahasa Indonesia yang ramah dan profesional
- Maksimal 3-4 paragraf pendek
- Fokus pada solusi untuk customer
- Jangan sebutkan HPP, margin, atau detail internal toko"""

            resp = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={"Content-Type": "application/json"},
                json={
                    "model": "claude-sonnet-4-6",
                    "max_tokens": 600,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=20,
            )
            data = resp.json()
            text = "".join(b["text"] for b in data.get("content",[]) if b.get("type")=="text")
            return text.strip() if text else _fallback_answer(query)
        except Exception as e:
            logger.warning(f"AI knowledge answer failed: {e}")
            return _fallback_answer(query)

    @staticmethod
    def _find_upsell(query: str, df: pd.DataFrame, category_hint: str) -> list[dict]:
        """Find upsell/cross-sell opportunities based on query context."""
        upsell_map = {
            "printer":   ["tinta","kertas","kabel usb","flash disk"],
            "laptop":    ["mouse","tas laptop","cooling pad","headset","ssd"],
            "monitor":   ["kabel hdmi","kabel display","speaker","webcam"],
            "keyboard":  ["mouse","mousepad","wrist rest"],
            "mouse":     ["mousepad","keyboard","wrist rest"],
            "pc":        ["ups","monitor","keyboard","mouse","headset"],
            "headset":   ["microphone","sound card","headset stand"],
            "webcam":    ["microphone","lighting","tripod"],
            "router":    ["kabel lan","access point","switch"],
        }

        cat_lower = category_hint.lower()
        query_lower = query.lower()

        # Find matching upsell categories
        upsell_cats = []
        for key, suggestions in upsell_map.items():
            if key in cat_lower or key in query_lower:
                upsell_cats.extend(suggestions)

        if not upsell_cats:
            return []

        # Find matching products in stock
        results = []
        for _, row in df.iterrows():
            if row.get("total_stok", 0) <= 0:
                continue
            name_lower = str(row.get("nama_barang","")).lower()
            for cat in upsell_cats:
                if cat in name_lower:
                    results.append({
                        "nama": str(row.get("nama_barang","")),
                        "h1": float(row.get("h1", 0)),
                        "stok": int(row.get("total_stok",0)),
                        "runrate": float(row.get("runrate_bulanan",0)),
                        "upsell_category": cat,
                    })
                    break

        results.sort(key=lambda x: -x["runrate"])
        return results[:4]

    @staticmethod
    def _extract_compat_notes(answer: str) -> list[str]:
        """Extract key compatibility notes from AI answer."""
        notes = []
        lines = answer.split("\n")
        for line in lines:
            line = line.strip()
            if line and len(line) > 20 and any(kw in line.lower() for kw in
                    ["cocok","kompatibel","support","compatible","pastikan","perhatikan","cek"]):
                notes.append(line[:120])
        return notes[:3]


def _fallback_answer(query: str) -> str:
    return (f"Untuk pertanyaan '{query}', silakan cek katalog produk KLA atau hubungi "
            f"tim teknis kami untuk mendapatkan rekomendasi yang tepat sesuai kebutuhan customer.")
