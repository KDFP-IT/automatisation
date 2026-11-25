#!/usr/bin/env python3
"""Export match results as GRAND-Smeta LocalEstimate XML (.gge).

Usage:
    python export_gge.py --match-id <id> --api ... --token ... --out out.gge
      [--name ...] [--num ...]

 takes top-1 candidate per work row, rescales VOR quantities into the norm's
 unit (108,66 м³ + норма 100 м3 -> Quantity 1.0866, formula "108,66 / 100").
 Material / not_found / error rows are skipped. Statuses live in the XLSX;
 the .gge carries only positions GRAND can price from its own base.
"""
import argparse
import json
import re
import urllib.request
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

UNIT_ALIASES = {
    "м3": "м3", "м³": "м3", "м^3": "м3",
    "м2": "м2", "м²": "м2",
    "м": "м", "км": "км",
    "т": "т", "кг": "кг",
    "шт": "шт", "компл": "компл",
    "1000 м3": "м3", "100 м3": "м3", "100 м2": "м2", "10 м2": "м2",
    "100 м": "м", "1000 м": "м",
    "км пути": "км", "км": "км",
    "1000 т": "т", "100 т": "т",
    "100 шт": "шт", "10 шт": "шт",
    "чел.-ч": "чел.-ч", "маш.-ч": "маш.-ч",
}

# (base_unit, factor_to_base)
SCALE = [
    (re.compile(r"^1000\s*(м3|м2|м|т|шт)$"), 1000.0),
    (re.compile(r"^100\s*(м3|м2|м|т|шт)$"), 100.0),
    (re.compile(r"^10\s*(м2|м|шт)$"), 10.0),
    (re.compile(r"^(м3|м2|м|км|т|кг|шт|компл|чел\.-ч|маш\.-ч)$"), 1.0),
]

LENGTH = {"м": 1.0, "км": 1000.0}
MASS = {"кг": 1.0, "т": 1000.0}


def parse_unit(text: str) -> tuple[str, float]:
    """Norm/VOR unit -> (base unit, quantity multiplier)."""
    raw = (text or "").strip().lower().replace("³", "3").replace("²", "2")
    for candidate in (raw, UNIT_ALIASES.get(raw, raw)):
        for pattern, factor in SCALE:
            match = pattern.match(candidate)
            if match:
                return match.group(1), factor
    raise ValueError(f"unknown unit: {text!r}")


def convert(quantity: float, from_unit: str, to_unit: str) -> tuple[float, str]:
    """VOR qty/unit -> qty in norm unit + formula string."""
    from_base, from_mul = parse_unit(from_unit)
    to_base, to_mul = parse_unit(to_unit)
    if from_base == to_base:
        value = quantity * from_mul / to_mul
    elif from_base in LENGTH and to_base in LENGTH:
        value = quantity * from_mul * LENGTH[from_base] / (to_mul * LENGTH[to_base])
    elif from_base in MASS and to_base in MASS:
        value = quantity * from_mul * MASS[from_base] / (to_mul * MASS[to_base])
    else:
        raise ValueError(f"incompatible units: {from_unit!r} -> {to_unit!r}")
    formula = f"{quantity} / {to_mul / from_mul:g}" if abs(to_mul - from_mul) > 1e-9 \
        else f"{quantity}"
    if from_base in LENGTH and to_base in LENGTH and from_base != to_base:
        formula = f"{quantity} / {to_mul * LENGTH[to_base] / (from_mul * LENGTH[from_base]):g}"
    if from_base in MASS and to_base in MASS and from_base != to_base:
        formula = f"{quantity} / {to_mul * MASS[to_base] / (from_mul * MASS[from_base]):g}"
    return round(value, 6), formula.replace(".", ",")


def build_gge(rows: list[dict], name: str, num: str) -> bytes:
    root = Element("Construction")
    root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    root.set("xsi:noNamespaceSchemaLocation",
             "LocalEstimateResourceIndexMethod-3_01.xsd")
    meta = SubElement(root, "Meta")
    soft = SubElement(meta, "Soft")
    SubElement(soft, "Name").text = "ГРАНД-Смета"
    SubElement(soft, "Version").text = "2026.3 Windows x64"
    file_el = SubElement(meta, "File")
    SubElement(file_el, "Type").text = "ЛС"
    SubElement(file_el, "Version").text = "3.01"
    SubElement(root, "Num").text = num
    SubElement(root, "Name").text = name
    obj = SubElement(root, "Object")
    SubElement(obj, "Num").text = num
    SubElement(obj, "Name").text = name
    estimate = SubElement(obj, "Estimate")
    positions = SubElement(estimate, "Positions")
    pos_no = 0
    for row in rows:
        cands = row.get("candidates") or []
        if row.get("skipped") or not cands:
            continue
        cand = cands[0]
        try:
            qty = float(str(row.get("quantity", "")).replace(",", ".").replace(" ", ""))
            value, formula = convert(qty, row.get("unit", ""), cand.get("unit", ""))
        except (ValueError, TypeError):
            continue
        pos_no += 1
        cost = SubElement(positions, "Cost")
        SubElement(cost, "Num").text = str(pos_no)
        SubElement(cost, "Prefix").text = "ГЭСН"
        SubElement(cost, "Code").text = cand["code"]
        SubElement(cost, "Name").text = cand.get("title", "")
        SubElement(cost, "Quantity").text = str(value).replace(".", ",")
        SubElement(cost, "QuantityFormula").text = formula
        SubElement(cost, "QuantityTotal").text = str(value).replace(".", ",")
        SubElement(cost, "Unit").text = cand.get("unit", "")
    xml = tostring(root, encoding="utf-8")
    pretty = minidom.parseString(xml).toprettyxml(indent="  ", encoding="utf-8")
    pretty = b"\n".join(line for line in pretty.split(b"\n") if line.strip())
    return b'<?xml version="1.0" encoding="utf-8"?>\r\n' + pretty.split(b"?>", 1)[1]


def main():
    parser = argparse.ArgumentParser(description="Export match results as .gge")
    parser.add_argument("--api", required=True)
    parser.add_argument("--token", default="")
    parser.add_argument("--match-id", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--name", default="Подбор ГЭСН из ВОР")
    parser.add_argument("--num", default="ЛСР-ИИ")
    args = parser.parse_args()

    req = urllib.request.Request(
        f"{args.api.rstrip('/')}/api/v1/match/{args.match_id}",
        headers={"Authorization": f"Bearer {args.token}"} if args.token else {})
    rows = json.loads(urllib.request.urlopen(req, timeout=60).read())["rows"]
    data = build_gge(rows, args.name, args.num)
    with open(args.out, "wb") as handle:
        handle.write(data)
    work = [r for r in rows if not r.get("skipped")]
    print(f"rows: {len(rows)}, work: {len(work)}, bytes: {len(data)}")


if __name__ == "__main__":
    main()
