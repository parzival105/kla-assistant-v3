"""lib/python/pc_builder_ai.py — AI explanation for PC builds."""
import os, json, requests, logging
logger = logging.getLogger(__name__)

def generate_explanation(build, customer_notes="") -> str:
    try:
        safe_comps = [{"tipe":c.kategori_label,"nama":c.nama,"harga":f"Rp {c.selling_price:,.0f}"} for c in build.components]
        compat = "\n".join(f"- {n}" for n in build.compatibility_notes) or "- Semua komponen kompatibel."
        prompt = f"""Kamu adalah konsultan PC di KLA Computer. Jelaskan build ini untuk customer.
BUILD: {build.build_type} | Budget: Rp {build.budget:,.0f} | Total: Rp {build.total_price:,.0f}
KOMPONEN: {json.dumps(safe_comps, ensure_ascii=False)}
KOMPATIBILITAS: {compat}
KEBUTUHAN: {customer_notes or "Tidak ada catatan."}
Tulis penjelasan singkat dalam Bahasa Indonesia (3-4 paragraf), fokus pada manfaat untuk customer. Jangan sebutkan HPP/margin."""

        r = requests.post("https://api.anthropic.com/v1/messages",
            headers={"Content-Type":"application/json","x-api-key":os.environ.get("ANTHROPIC_API_KEY","")},
            json={"model":"claude-sonnet-4-6","max_tokens":600,"messages":[{"role":"user","content":prompt}]},
            timeout=25)
        data = r.json()
        return "".join(b["text"] for b in data.get("content",[]) if b.get("type")=="text").strip()
    except Exception as e:
        logger.warning(f"AI explanation failed: {e}")
        return f"Build {build.build_type} total Rp {build.total_price:,.0f} dari {len(build.components)} komponen stok KLA."
