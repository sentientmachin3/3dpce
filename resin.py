from pathlib import Path
import struct


def parse_goo(path: Path) -> dict[str, float]:
    header_size = 0x2FB95
    d = open(path, "rb").read()
    anchor = d.rfind(b"\x24\x00", header_size - 64, header_size)
    off = anchor - 16
    printing_time = struct.unpack_from(">I", d, off)[0]  # seconds
    total_volume = struct.unpack_from(">f", d, off + 4)[0]  # mm^3
    total_weight = struct.unpack_from(">f", d, off + 8)[0]  # grams

    return {
        "printTimeMinutes": round(printing_time / 60),
        # "volume_mm3": total_volume,
        "modelWeightGrams": total_weight,
    }
