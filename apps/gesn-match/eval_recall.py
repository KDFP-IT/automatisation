#!/usr/bin/env python3
"""Recall@3 / top-1 match results against a ГРАНД-Смета ЛСР file (ground truth).

Usage:
    python eval_recall.py --dsn ... --edition-id ... --match-id <job> \
        --lsr /path/to.lsr.xlsx --api http://127.0.0.1:8080/gesn-match --token ...

Matches VOR rows to truth rows by token overlap (>= 0.2), then checks whether
the estimator-assigned code is within top-3 candidates.
"""
import argparse
import json
import re
import urllib.request
from collections import Counter

from openpyxl import load_workbook

STOP = {'и', 'в', 'на', 'с', 'по', 'из', 'для', 'до', 'от'}


def toks(text: str) -> set:
    return set(re.findall(r'[а-яa-z0-9]+', text.lower())) - STOP


def norm_code(raw: str) -> str:
    return re.sub(r'^(ГЭСНм?р?|ФЕР)', '', raw.strip()).strip()


def load_truth(path: str) -> list:
    book = load_workbook(path, read_only=True, data_only=True)
    sheet = book[book.sheetnames[0]]
    truth = []
    for row in sheet.iter_rows(values_only=True):
        num = str(row[0] or '').strip()
        ob = str(row[1] or '').strip()
        name = str(row[2] or '').strip()
        if num and num[0].isdigit() and ob and re.match(r'^(ГЭСНм?р?|ФЕР)', ob):
            truth.append((toks(name), norm_code(ob), name[:60]))
    return truth


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", required=True)
    parser.add_argument("--token", default="")
    parser.add_argument("--match-id", required=True)
    parser.add_argument("--lsr", required=True)
    args = parser.parse_args()

    req = urllib.request.Request(
        f"{args.api.rstrip('/')}/api/v1/match/{args.match_id}",
        headers={"Authorization": f"Bearer {args.token}"} if args.token else {},
    )
    rows = json.loads(urllib.request.urlopen(req, timeout=60).read())["rows"]
    truth = [(t, c, n) for t, c, n in load_truth(args.lsr)]
    print(f"rows: {len(rows)}, truth positions: {len(truth)}")

    hits3 = hits1 = mapped = skipped = 0
    misses = []
    for row in rows:
        if row.get("skipped") == "material":
            skipped += 1
            continue
        vt = toks(row["name"])
        best, overlap = None, 0.0
        for tt, code, _ in truth:
            score = len(vt & tt) / max(1, len(vt | tt))
            if score > overlap:
                best, overlap = code, score
        if overlap < 0.2:
            continue
        mapped += 1
        codes = [c["code"] for c in row.get("candidates", [])]
        hits3 += best in codes
        hits1 += (codes[:1] == [best])
        if best not in codes:
            misses.append((best, row["name"][:50], codes))
    work = [r for r in rows if r.get("skipped") != "material"]
    print(f"work rows: {len(work)}, mapped: {mapped}, skipped materials: {skipped}")
    print(f"RECALL@3: {hits3}/{mapped}  TOP1: {hits1}/{mapped}")
    for code, name, codes in misses:
        print(f"MISS: {code} | {name} | got: {codes}")
    print(Counter(c["status"] for r in rows for c in r.get("candidates", [])))


if __name__ == "__main__":
    main()
