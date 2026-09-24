from pathlib import Path
import re


def parse_time_to_minutes(time_str):
    hours = re.search(r"(\d+)\s*h", time_str)
    minutes = re.search(r"(\d+)\s*m", time_str)
    seconds = re.search(r"(\d+)\s*s", time_str)

    h = float(hours.group(1)) if hours else 0.0
    m = float(minutes.group(1)) if minutes else 0.0
    s = float(seconds.group(1)) if seconds else 0.0

    return round(h * 60.0 + m + (s / 60.0), 4)


def parse_gcode(file_path: Path) -> dict[str, float]:
    header_bytes = 10_000
    footer_bytes = 500
    file_size = file_path.stat().st_size

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        header_text = f.read(header_bytes)
        f.seek(file_size - footer_bytes)
        footer_text = f.read()

    printing_time_minutes = None
    filament_used_g = None

    # printing time
    for line in header_text.splitlines():
        if "model printing time:" in line:
            match = re.search(r"model printing time:\s*([^;]+)", line)
            if match:
                printing_time_minutes = parse_time_to_minutes(match.group(1).strip())
                break

    # filament weight in grams
    for line in footer_text.splitlines():
        if "filament used [g]" in line:
            match = re.search(r"filament used \[g\]\s*=\s*([0-9.]+)", line)
            if match:
                filament_used_g = float(match.group(1))
                break
    if printing_time_minutes is not None and filament_used_g is not None:
        return {
            "printTimeMinutes": printing_time_minutes,
            "modelWeightGrams": filament_used_g,
        }
    else:
        raise RuntimeError("Didn't find required info in gcode")
