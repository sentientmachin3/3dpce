#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path
import configparser
import re
import struct
import resin
import fdm

DEPRECIATION_FACTOR_PER_MINUTE = 0.00125


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="3dpce.py",
        description="Estimate costs for filament prints",
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
        "-s",
        "--section",
        dest="section",
        metavar="SECTION",
        required=False,
        default="DEFAULT",
        type=str,
        help="Section of the config file to use",
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
        "layers_file",
        metavar="LAYERS_FILE_PATH",
        type=Path,
        help="Path to the gcode file.",
    )

    return parser.parse_args(argv)


def parse_config(file_path: Path, section: str = "DEFAULT") -> dict[str, float]:
    cp = configparser.ConfigParser()
    cp.read(file_path)
    setup = cp[section]
    return {
        "materialCostPerGram": float(setup["material_cost_euros_per_gram"]),
        "printerNominalPower": float(setup["printer_power_w"]) / 1000,
        "electricityCostPerKwm": float(setup["ac_cost_euros_kwh"]) / 60,
        "marginFactor": float(setup["margin_percent"]) / 100,
        "prepCost": float(setup["prep_cost"]),
    }


def main(argv=None):
    args = parse_args(argv)
    config_path = args.config
    section = args.section
    layers_file_path: Path = args.layers_file
    margin = args.margin

    config = parse_config(config_path, section)
    if layers_file_path.suffix == ".goo":
        layers = resin.parse_goo(layers_file_path)
    elif layers_file_path.suffix == ".gcode":
        layers = fdm.parse_gcode(layers_file_path)
    else:
        raise RuntimeError(f"unknown file ext {layers_file_path.suffix}")

    # calculations in euros and minutes on a per-minute basis
    print_time_mins = layers["printTimeMinutes"]
    net_material = round(config["materialCostPerGram"] * layers["modelWeightGrams"], 2)
    margin_factor = margin / 100 if margin is not None else config["marginFactor"]
    machine_costs = round(
        print_time_mins
        * config["printerNominalPower"]
        * config["electricityCostPerKwm"],
        2,
    )
    depreciation = round(DEPRECIATION_FACTOR_PER_MINUTE * print_time_mins, 2)
    net_total = net_material + machine_costs + config["prepCost"] + depreciation
    total = round(net_total + (net_total * margin_factor), 2)

    print(f"""
    ===============
    Material costs: {net_material}
    Machine costs: {machine_costs}
    Depreciation: {depreciation}
    Labour: {config["prepCost"]}
    
    TOTAL: {total} (margin {margin_factor * 100} %)
    ===============
    """)


if __name__ == "__main__":
    main(sys.argv[1:])
