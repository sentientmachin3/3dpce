#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path
import configparser
import re

LABOUR_PREP_COST = 1.20
DEPRECIATION_FACTOR_PER_MINUTE = 0.00125


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="3dpce.py",
        description="Estimantes costs for FDP prints",
    )

    parser.add_argument(
        "-c",
        "--config",
        dest="config",
        metavar="PATH",
        required=True,
        type=Path,
        help="Path to the configuration file",
    )

    parser.add_argument(
        "-m",
        "--margin",
        dest="margin",
        metavar="MARGIN",
        required=False,
        type=float,
        help="Margin in percentage points",
    )

    parser.add_argument(
        "gcode",
        metavar="GCODE_PATH",
        type=Path,
        help="Path to the gcode file.",
    )

    return parser.parse_args(argv)


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


def parse_config(file_path: Path) -> dict[str, float]:
    cp = configparser.ConfigParser()
    cp.read(file_path)
    default = cp["DEFAULT"]
    return {
        "filamentCostPerGram": float(default["filament_cost_euros_per_gram"]),
        "printerNominalPower": float(default["printer_power_w"]) / 1000,
        "electricityCostPerKwm": float(default["ac_cost_euros_kwh"]) / 60,
        "marginFactor": float(default["margin_percent"]) / 100,
    }


def main(argv=None):
    args = parse_args(argv)
    config_path = args.config
    gcode_path = args.gcode
    margin = args.margin

    config = parse_config(config_path)
    gcode = parse_gcode(gcode_path)

    # calculations in euros and minutes on a per-minute basis
    print_time_mins = gcode["printTimeMinutes"]
    net_material = round(config["filamentCostPerGram"] * gcode["modelWeightGrams"], 2)
    margin_factor = margin / 100 if margin is not None else config["marginFactor"]
    machine_costs = round(
        print_time_mins
        * config["printerNominalPower"]
        * config["electricityCostPerKwm"],
        2,
    )
    depreciation = round(DEPRECIATION_FACTOR_PER_MINUTE * print_time_mins, 2)
    net_total = net_material + machine_costs + LABOUR_PREP_COST + depreciation
    total = round(net_total + (net_total * margin_factor), 2)

    print(f"""
    ===============
    Material costs: {net_material}
    Machine costs: {machine_costs}
    Depreciation: {depreciation}
    Labour: {LABOUR_PREP_COST}
    
    TOTAL: {total} (margin {margin_factor * 100} %)
    ===============
    """)


if __name__ == "__main__":
    main(sys.argv[1:])
