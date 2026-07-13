"""
modules/sales_assistant/search.py
===================================
Universal Product Search Engine — mencari produk dari stock inventory
berdasarkan natural language query, dengan filtering harga sesuai role.

Price visibility rules:
  Sales       → harga jual (H1) only, NO HPP, NO margin
  Store Leader→ harga jual (H1) + margin %
  Area Manager→ harga jual (H1) + margin % + HPP
  Super Admin → all data
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Optional
import pandas as pd
from lib.python.config_vercel import (
    ROLE_SALES, ROLE_STORE_LEADER, ROLE_AREA_MANAGER, ROLE_SUPER_ADMIN,
    BRANCH_FULL_NAMES, ALL_BRANCHES,
)

logger = logging.getLogger(__name__)


@dataclass
class ProductResult:
    """A single product search result with role-filtered pricing."""
    nama_barang: str
    kategori: str
    segment: str
    brand: str
    harga_jual: float          # H1 — always shown
    margin_persen: Optional[float]   # shown to Store Leader+
    hpp: Optional[float]             # shown to Area Manager+
    total_stok: int
    runrate_bulanan: float
    stock_by_branch: dict[str, int] = field(default_factory=dict)  # branch -> qty
    score: float = 0.0               # relevance score for ranking


@dataclass
class SearchResult:
    query: str
    intent_category: str
    products: list[ProductResult]
    total_found: int
    search_notes: list[str] = field(default_factory=list)


class ProductSearchEngine:
    """
    Searches inventory DataFrame for products matching a natural language
    query, ranks by relevance (runrate × stock × margin), and applies
    role-based price visibility.
    """

    ROLE_PRICE_VISIBILITY = {
        ROLE_SALES:        {"hpp": False, "margin": False},
        ROLE_STORE_LEADER: {"hpp": False, "margin": True},
        ROLE_AREA_MANAGER: {"hpp": True,  "margin": True},
        ROLE_SUPER_ADMIN:  {"hpp": True,  "margin": True},
    }

    def search(
        self,
        query: str,
        df: pd.DataFrame,
        stock_columns: dict[str, str],
        role: str,
        category_hint: str = "",
        brand_hint: str = "",
        budget_hint: Optional[float] = None,
        use_case_hint: str = "",
        top_n: int = 8,
    ) -> SearchResult:
        """
        Search products matching the query with role-filtered pricing.

        Args:
            query: Natural language query from sales.
            df: Full enriched inventory DataFrame.
            stock_columns: branch_code -> column_name mapping.
            role: Current user role for price visibility.
            category_hint: Category keyword extracted by intent engine.
            brand_hint: Brand keyword extracted by intent engine.
            budget_hint: Max price filter in Rupiah.
            use_case_hint: Use case keyword (gaming, kantor, etc).
            top_n: Number of top results to return.

        Returns:
            SearchResult with ranked ProductResult list.
        """
        notes: list[str] = []
        working = df.copy()

        # Step 1: Text search across nama_barang, kategori, segment, brand
        query_terms = self._tokenize(query)
        cat_terms   = self._tokenize(category_hint)
        brand_terms = self._tokenize(brand_hint) if brand_hint else []
        use_terms   = self._tokenize(use_case_hint) if use_case_hint else []

        all_terms = list(set(query_terms + cat_terms + brand_terms + use_terms))

        if all_terms:
            mask = working.apply(
                lambda row: self._row_matches(row, all_terms), axis=1
            )
            matched = working[mask].copy()
        else:
            matched = working.copy()

        if matched.empty:
            # Fallback: looser search using only category_hint
            if category_hint:
                cat_lower = category_hint.lower()
                fb_mask = working["nama_barang"].str.lower().str.contains(cat_lower, na=False)
                matched = working[fb_mask].copy()
                notes.append(f"Pencarian diperluas menggunakan kategori '{category_hint}'.")

        if matched.empty:
            return SearchResult(query=query, intent_category=category_hint,
                                products=[], total_found=0,
                                search_notes=["Tidak ada produk yang cocok dengan pencarian ini."])

        # Step 2: Budget filter
        if budget_hint and budget_hint > 0:
            price_col = "h1" if "h1" in matched.columns else "harga_rekomendasi"
            before = len(matched)
            matched = matched[matched[price_col] <= budget_hint * 1.15]  # 15% tolerance
            if len(matched) < before:
                notes.append(f"Difilter berdasarkan budget ≤ Rp {budget_hint:,.0f} (toleransi 15%).")
            if matched.empty:
                matched = working[working[price_col] <= budget_hint * 1.5].copy()
                notes.append("Budget diperlonggar 50% karena tidak ada produk dalam budget ketat.")

        # Step 3: Relevance scoring
        matched = self._score_results(matched, all_terms)
        matched = matched.nlargest(top_n, "relevance_score")

        # Step 4: Build result objects with role-filtered pricing
        visibility = self.ROLE_PRICE_VISIBILITY.get(role, {"hpp": False, "margin": False})
        products = []
        for _, row in matched.iterrows():
            # Build per-branch stock from detected stock columns
            branch_stock = {}
            for branch, col in stock_columns.items():
                # col might still be the raw column name if df still has it
                qty = 0
                if col in row.index:
                    qty = int(float(row.get(col, 0) or 0))
                if qty > 0:
                    branch_stock[branch] = qty

            # If no branch stock found via column map, try direct branch name columns
            if not branch_stock:
                from lib.python.config_vercel import ALL_BRANCHES
                for branch in ALL_BRANCHES:
                    for possible_col in [branch, branch.upper(), branch.lower()]:
                        if possible_col in row.index:
                            qty = int(float(row.get(possible_col, 0) or 0))
                            if qty > 0:
                                branch_stock[branch] = qty
                            break

            hpp_val    = float(row.get("hpp", 0) or 0)
            h1_val     = float(row.get("h1", 0) or row.get("harga_rekomendasi", hpp_val) or 0)
            margin_pct = float(row.get("margin_persen", 0) or 0)

            products.append(ProductResult(
                nama_barang=str(row.get("nama_barang", "")),
                kategori=str(row.get("kategori_produk", row.get("kategori", ""))),
                segment=str(row.get("segment", "")),
                brand=str(row.get("brand", "")),
                harga_jual=h1_val,
                margin_persen=margin_pct if visibility["margin"] else None,
                hpp=hpp_val if visibility["hpp"] else None,
                total_stok=int(row.get("total_stok", 0) or 0),
                runrate_bulanan=float(row.get("runrate_bulanan", 0) or 0),
                stock_by_branch=branch_stock,
                score=float(row.get("relevance_score", 0) or 0),
            ))

        return SearchResult(
            query=query, intent_category=category_hint,
            products=products, total_found=len(matched),
            search_notes=notes,
        )

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Split text into lowercase tokens, min 2 chars."""
        import re
        tokens = re.sub(r"[^a-z0-9\s]", " ", text.lower()).split()
        return [t for t in tokens if len(t) >= 2]

    @staticmethod
    def _row_matches(row: pd.Series, terms: list[str]) -> bool:
        """Check if a product row matches any search term."""
        searchable = " ".join([
            str(row.get("nama_barang", "")),
            str(row.get("kategori_produk", "")),
            str(row.get("segment", "")),
            str(row.get("brand", "")),
        ]).lower()
        return any(term in searchable for term in terms)

    @staticmethod
    def _score_results(df: pd.DataFrame, terms: list[str]) -> pd.DataFrame:
        """
        Score each product by relevance:
        - Term match frequency in name (higher = more relevant)
        - Runrate (fast movers ranked higher)
        - Total stock (in-stock products ranked higher)
        - Margin (higher margin = slightly preferred)
        """
        df = df.copy()

        def _term_score(name: str) -> float:
            name_lower = str(name).lower()
            return sum(2.0 if term in name_lower else 0.0 for term in terms)

        name_score   = df["nama_barang"].apply(_term_score)
        rr_score     = df["runrate_bulanan"].clip(0, 50) / 50     # 0–1
        stock_score  = (df["total_stok"] > 0).astype(float)       # binary
        margin_score = df["margin_persen"].clip(0, 40) / 40 if "margin_persen" in df.columns else 0

        df["relevance_score"] = (
            name_score   * 0.50 +
            rr_score     * 0.25 +
            stock_score  * 0.15 +
            margin_score * 0.10
        )
        return df


def search_products(
    query: str,
    df: pd.DataFrame,
    stock_columns: dict,
    role: str,
    category_hint: str = "",
    brand_hint: str = "",
    budget_hint: Optional[float] = None,
    use_case_hint: str = "",
    top_n: int = 8,
) -> SearchResult:
    """Convenience wrapper for ProductSearchEngine.search()."""
    return ProductSearchEngine().search(
        query=query, df=df, stock_columns=stock_columns, role=role,
        category_hint=category_hint, brand_hint=brand_hint,
        budget_hint=budget_hint, use_case_hint=use_case_hint, top_n=top_n,
    )
