"""
modules/pc_consultant/compatibility.py
========================================
Compatibility engine berdasarkan Database_Kesesuaian_Komponen_PC_Intel_AMD_2026.xlsx

Rules:
  - CPU socket HARUS cocok dengan Motherboard socket
  - RAM type (DDR3/DDR4/DDR5) HARUS sesuai platform
  - PSU wattage cukup untuk konfigurasi
  - Setiap komponen dilengkapi info stok per cabang
"""
from __future__ import annotations
import re
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# ─── Socket Map (dari sheet Socket + Intel CPU + AMD CPU) ────────────────────
SOCKET_MAP: dict[str, str] = {
    # Intel — by generation keyword
    "gen 4": "LGA1150", "gen 5": "LGA1150",
    "gen 6": "LGA1151", "gen 7": "LGA1151",
    "gen 8": "LGA1151", "gen 9": "LGA1151",
    "gen 10": "LGA1200", "gen 11": "LGA1200",
    "gen 12": "LGA1700", "gen 13": "LGA1700", "gen 14": "LGA1700",
    "core ultra 200": "LGA1851", "arrow lake": "LGA1851",
    # Intel — by CPU name keywords
    "haswell": "LGA1150", "broadwell": "LGA1150",
    "skylake": "LGA1151", "kaby lake": "LGA1151",
    "coffee lake": "LGA1151", "comet lake": "LGA1200",
    "rocket lake": "LGA1200", "alder lake": "LGA1700",
    "raptor lake": "LGA1700",
    # Intel — by generation number in name (i3/i5/i7/i9 GEN)
    "i3-12": "LGA1700", "i5-12": "LGA1700", "i7-12": "LGA1700", "i9-12": "LGA1700",
    "i3-13": "LGA1700", "i5-13": "LGA1700", "i7-13": "LGA1700", "i9-13": "LGA1700",
    "i3-14": "LGA1700", "i5-14": "LGA1700", "i7-14": "LGA1700", "i9-14": "LGA1700",
    "i3-10": "LGA1200", "i5-10": "LGA1200", "i7-10": "LGA1200", "i9-10": "LGA1200",
    "i3-11": "LGA1200", "i5-11": "LGA1200", "i7-11": "LGA1200", "i9-11": "LGA1200",
    "i3-8":  "LGA1151", "i5-8":  "LGA1151", "i7-8":  "LGA1151", "i9-8":  "LGA1151",
    "i3-9":  "LGA1151", "i5-9":  "LGA1151", "i7-9":  "LGA1151", "i9-9":  "LGA1151",
    "i3-6":  "LGA1151", "i5-6":  "LGA1151", "i7-6":  "LGA1151",
    "i3-7":  "LGA1151", "i5-7":  "LGA1151", "i7-7":  "LGA1151",
    "i3-4":  "LGA1150", "i5-4":  "LGA1150", "i7-4":  "LGA1150",
    "i3-5":  "LGA1150", "i5-5":  "LGA1150", "i7-5":  "LGA1150",
    # AMD — by socket/series
    "am4": "AM4", "am5": "AM5", "fm2+": "FM2+", "fm2": "FM2",
    "ryzen 9000": "AM5", "ryzen 8000": "AM5", "ryzen 7000": "AM5",
    "ryzen 5000": "AM4", "ryzen 4000": "AM4", "ryzen 3000": "AM4",
    "ryzen 2000": "AM4", "ryzen 1000": "AM4",
    "athlon 200": "AM4", "athlon 300": "AM4",
}

# ─── RAM Type per Platform ────────────────────────────────────────────────────
PLATFORM_RAM: dict[str, list[str]] = {
    "LGA1150": ["DDR3"],
    "LGA1151": ["DDR4", "DDR3"],   # Gen6 support DDR3L juga
    "LGA1200": ["DDR4"],
    "LGA1700": ["DDR4", "DDR5"],   # board dependent
    "LGA1851": ["DDR5"],
    "FM2":     ["DDR3"],
    "FM2+":    ["DDR3"],
    "AM4":     ["DDR4"],
    "AM5":     ["DDR5"],
}

# ─── Chipset compatibel per socket ───────────────────────────────────────────
SOCKET_CHIPSETS: dict[str, list[str]] = {
    "LGA1150": ["H81","B85","H87","Z87","H97","Z97"],
    "LGA1151": ["H110","B150","H170","Z170","H270","B250","Z270"],
    "LGA1151": ["H310","B360","H370","Z370","B365","Z390"],   # gen8-9 override
    "LGA1200": ["H410","B460","H470","Z490","H510","B560","Z590"],
    "LGA1700": ["H610","B660","H670","Z690","B760","Z790","H810","B860","Z890"],
    "LGA1851": ["H810","B860","Z890"],
    "FM2":     ["A55","A75","A85X"],
    "FM2+":    ["A68H","A78","A88X"],
    "AM4":     ["A320","B350","X370","A520","B450","X470","B550","X570"],
    "AM5":     ["A620","B650","X670","B840","B850","X870"],
}

# ─── PSU minimum recommendation ──────────────────────────────────────────────
PSU_MIN_WATT: dict[str, int] = {
    "rtx 4090": 850, "rtx 4080": 750, "rtx 4070": 650, "rtx 4060": 550,
    "rtx 3090": 850, "rtx 3080": 750, "rtx 3070": 650, "rtx 3060": 550,
    "rx 7900": 800,  "rx 7800": 700,  "rx 7700": 600,  "rx 6800": 750,
    "rx 6700": 650,  "rx 6600": 550,
    "gtx 1660": 450, "gtx 1650": 350,
}


@dataclass
class CompatResult:
    cpu_socket: str = ""
    mb_socket: str = ""
    ram_type_detected: str = ""
    ram_compatible: bool = True
    socket_compatible: bool = True
    psu_ok: bool = True
    psu_recommended_watt: int = 0
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def get_cpu_socket(cpu_name: str) -> str:
    """Detect CPU socket dari nama CPU."""
    name = cpu_name.lower()
    # Try specific model number first (e.g. i5-12400)
    for key, socket in SOCKET_MAP.items():
        if key in name:
            return socket
    return ""


def get_mb_socket(mb_name: str) -> str:
    """Extract socket dari nama Motherboard."""
    name = mb_name.lower()
    socket_keywords = {
        "lga1851": "LGA1851", "lga1700": "LGA1700", "lga1200": "LGA1200",
        "lga1151": "LGA1151", "lga1150": "LGA1150",
        "am5": "AM5", "am4": "AM4", "fm2+": "FM2+", "fm2": "FM2",
    }
    for kw, socket in socket_keywords.items():
        if kw in name:
            return socket
    # Try chipset-based detection
    all_chipsets = {
        chip: sock for sock, chips in SOCKET_CHIPSETS.items() for chip in chips
    }
    for chipset, socket in all_chipsets.items():
        if chipset.lower() in name:
            return socket
    return ""


def get_ram_type(ram_name: str) -> str:
    """Detect RAM type dari nama produk."""
    name = ram_name.lower()
    if "ddr5" in name: return "DDR5"
    if "ddr4" in name: return "DDR4"
    if "ddr3l" in name: return "DDR3"
    if "ddr3" in name: return "DDR3"
    return ""


def check_compatibility(
    cpu_name: str,
    mb_name: str,
    ram_name: str = "",
    gpu_name: str = "",
    psu_name: str = "",
) -> CompatResult:
    """
    Run full compatibility check for a set of components.

    Returns CompatResult dengan notes (info) dan warnings (masalah).
    """
    result = CompatResult()

    # ── CPU ↔ Motherboard socket check ──────────────────────────────────────
    cpu_socket = get_cpu_socket(cpu_name)
    mb_socket  = get_mb_socket(mb_name)
    result.cpu_socket = cpu_socket
    result.mb_socket  = mb_socket

    if cpu_socket and mb_socket:
        if cpu_socket == mb_socket:
            result.socket_compatible = True
            result.notes.append(f"✅ CPU dan Motherboard kompatibel — socket {cpu_socket}.")
        else:
            result.socket_compatible = False
            result.warnings.append(
                f"⚠️ TIDAK KOMPATIBEL — CPU socket {cpu_socket} ≠ Motherboard socket {mb_socket}. "
                f"Ganti salah satu komponen."
            )
    elif cpu_socket:
        result.notes.append(f"ℹ️ CPU socket: {cpu_socket}. Pastikan motherboard mendukung {cpu_socket}.")
    elif mb_socket:
        result.notes.append(f"ℹ️ Motherboard socket: {mb_socket}.")

    # ── RAM type check ────────────────────────────────────────────────────────
    if ram_name:
        ram_type = get_ram_type(ram_name)
        result.ram_type_detected = ram_type
        active_socket = cpu_socket or mb_socket

        if ram_type and active_socket:
            supported = PLATFORM_RAM.get(active_socket, [])
            if ram_type in supported:
                result.ram_compatible = True
                result.notes.append(f"✅ RAM {ram_type} kompatibel dengan platform {active_socket}.")
            else:
                result.ram_compatible = False
                result.warnings.append(
                    f"⚠️ RAM {ram_type} TIDAK kompatibel dengan {active_socket}. "
                    f"Platform ini membutuhkan: {', '.join(supported)}."
                )
        elif ram_type:
            result.notes.append(f"ℹ️ RAM terdeteksi: {ram_type}.")

    # ── PSU adequacy check ────────────────────────────────────────────────────
    if psu_name and gpu_name:
        psu_watt = _extract_watt(psu_name)
        gpu_lower = gpu_name.lower()
        min_watt = 0
        for gpu_key, req in PSU_MIN_WATT.items():
            if gpu_key in gpu_lower:
                min_watt = req
                break

        if psu_watt and min_watt:
            result.psu_recommended_watt = min_watt
            if psu_watt >= min_watt:
                result.psu_ok = True
                result.notes.append(f"✅ PSU {psu_watt}W cukup untuk GPU ini (min {min_watt}W).")
            else:
                result.psu_ok = False
                result.warnings.append(
                    f"⚠️ PSU {psu_watt}W kurang untuk GPU ini. "
                    f"Direkomendasikan minimal {min_watt}W."
                )

    return result


def _extract_watt(psu_name: str) -> int:
    """Extract watt value from PSU name string."""
    m = re.search(r"(\d{3,4})\s*w", psu_name.lower())
    if m:
        return int(m.group(1))
    return 0
