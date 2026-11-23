#!/usr/bin/env python3
"""Import ФСНБ-2022 XML (ИАС ЦС) into the norms catalog.

Usage:
    python import_fsnb.py --dsn postgresql://... --edition-id gesn-2026-dop20 \\
        ГЭСН.xml [ГЭСНм.xml ...]

Collection is derived from the <base BaseType> attribute unless --collection
overrides it. Re-runnable: upserts on (code, edition_id).
"""
import argparse
import os
from xml.etree.ElementTree import iterparse

import psycopg

BATCH = 1000


def res_kind(code: str) -> str:
    if code.startswith("1-"):
        return "labor"
    if code.startswith("91."):
        return "machine"
    return "material"


def parse_work(work, ctx) -> dict:
    code = work.get("Code", "")
    end_name = (work.get("EndName") or "").strip()
    begin = (ctx["begin_name"] or "").rstrip(":").strip()
    title = f"{begin}: {end_name}".strip(": ") if begin else end_name
    unit = work.get("MeasureUnit", "")
    composition = [
        (item.get("Text") or "").strip()
        for content in work.findall("Content")
        for item in content.findall("Item")
        if (item.get("Text") or "").strip()
    ]
    resources = [
        {
            "code": r.get("Code", ""),
            "name": r.get("EndName"),
            "quantity": r.get("Quantity", ""),
            "kind": res_kind(r.get("Code", "")),
        }
        for rs in work.findall("Resources")
        for r in rs.findall("Resource")
    ]
    nrsp = [
        f"НР {i.get('Nr', '')} / СП {i.get('Sp', '')}".strip(" /")
        for nr in work.findall("NrSp")
        for i in nr.findall("ReasonItem")
    ]
    section_path = " / ".join(
        s for s in (ctx["sbornik"], ctx["razdel"], ctx["podrazdel"]) if s
    )
    return {
        "code": code,
        "collection": ctx["collection"],
        "table_code": ctx["table"],
        "title": title,
        "unit": unit,
        "work_composition": composition,
        "tech_conditions": nrsp,
        "edition_id": ctx["edition_id"],
        "source_ref": f"{ctx['filename']} :: {section_path} / {ctx['table']}".strip(" /"),
        "needs_review": not unit or not composition,
        "resources": resources,
    }

def refresh_ctx(ctx, stack):
    ctx["sbornik"] = ctx["razdel"] = ctx["podrazdel"] = ctx["table"] = ""
    for section_type, name, code in stack:
        label = f"{code} {name}".strip()
        if section_type == "Сборник":
            ctx["sbornik"] = label
        elif section_type == "Раздел":
            ctx["razdel"] = label
        elif section_type == "Подраздел":
            ctx["podrazdel"] = label
        elif section_type == "Таблица":
            ctx["table"] = code


def iter_works(path: str, collection: str | None, edition_id: str):
    filename = os.path.basename(path)
    ctx = {
        "filename": filename, "collection": collection, "edition_id": edition_id,
        "sbornik": "", "razdel": "", "podrazdel": "", "table": "",
        "begin_name": "",
    }
    base_attrs: dict = {}
    depth_sections: list[tuple[str, str, str]] = []  # (type, name, code)
    for event, elem in iterparse(path, events=("start", "end")):
        tag = elem.tag
        if event == "start":
            if tag == "base":
                base_attrs = dict(elem.attrib)
                if ctx["collection"] is None:
                    ctx["collection"] = base_attrs.get("BaseType", collection or "")
            elif tag == "Section":
                depth_sections.append((elem.get("Type", ""), elem.get("Name", ""), elem.get("Code", "")))
                refresh_ctx(ctx, depth_sections)
            elif tag == "NameGroup":
                ctx["begin_name"] = elem.get("BeginName", "")
        else:
            if tag == "Work":
                yield ("work", parse_work(elem, ctx))
                elem.clear()
            elif tag == "Decrees":
                decree = "; ".join(d.get("Name", "") for d in elem.findall("Decree"))
                yield ("edition", {
                    "id": edition_id,
                    "base_name": base_attrs.get("BaseName", ""),
                    "price_level": base_attrs.get("PriceLevel", ""),
                    "creation_date": f"{base_attrs.get('CreationDate', '')} {base_attrs.get('CreationTime', '')}".strip(),
                    "decree": decree,
                })
                elem.clear()
            elif tag == "NameGroup":
                ctx["begin_name"] = ""
                elem.clear()
            elif tag == "Section":
                depth_sections.pop()
                refresh_ctx(ctx, depth_sections)
                elem.clear()


UPSERT_EDITION = """INSERT INTO editions(id, base_name, price_level, creation_date, decree)
VALUES (%(id)s, %(base_name)s, %(price_level)s, %(creation_date)s, %(decree)s)
ON CONFLICT (id) DO UPDATE SET base_name=EXCLUDED.base_name,
  price_level=EXCLUDED.price_level, creation_date=EXCLUDED.creation_date,
  decree=EXCLUDED.decree"""

UPSERT_NORM = """INSERT INTO norms(code, collection, table_code, title, unit,
  work_composition, tech_conditions, edition_id, source_ref, needs_review, search_tsv)
VALUES (%(code)s, %(collection)s, %(table_code)s, %(title)s, %(unit)s,
  %(work_composition)s, %(tech_conditions)s, %(edition_id)s, %(source_ref)s,
  %(needs_review)s,
  to_tsvector('russian', unaccent(%(title)s || ' ' || array_to_string(%(work_composition)s::text[], ' '))))
ON CONFLICT (code) DO UPDATE SET collection=EXCLUDED.collection,
  table_code=EXCLUDED.table_code, title=EXCLUDED.title, unit=EXCLUDED.unit,
  work_composition=EXCLUDED.work_composition, tech_conditions=EXCLUDED.tech_conditions,
  edition_id=EXCLUDED.edition_id, source_ref=EXCLUDED.source_ref,
  needs_review=EXCLUDED.needs_review, search_tsv=EXCLUDED.search_tsv"""

UPSERT_RES = """INSERT INTO norm_resources(norm_code, res_code, res_name, quantity, res_kind)
VALUES (%(norm_code)s, %(res_code)s, %(res_name)s, %(quantity)s, %(res_kind)s)
ON CONFLICT (norm_code, res_code, quantity) DO UPDATE SET
  res_name=EXCLUDED.res_name, res_kind=EXCLUDED.res_kind"""


def run(dsn: str, edition_id: str, files: list[str], collection: str | None):
    works = 0
    with psycopg.connect(dsn) as con:
        for path in files:
            norms_batch, res_batch = [], []
            for kind, payload in iter_works(path, collection, edition_id):
                if kind == "edition":
                    con.execute(UPSERT_EDITION, payload)
                    continue
                if not payload["code"]:
                    continue
                norms_batch.append(payload)
                for res in payload["resources"]:
                    res_batch.append({"norm_code": payload["code"], **res})
                if len(norms_batch) >= BATCH:
                    for row in norms_batch:
                        con.execute(UPSERT_NORM, row)
                    for row in res_batch:
                        con.execute(UPSERT_RES, row)
                    works += len(norms_batch)
                    norms_batch, res_batch = [], []
                    con.commit()
                    print(f"  ... {works} norms", flush=True)
            for row in norms_batch:
                con.execute(UPSERT_NORM, row)
            for row in res_batch:
                con.execute(UPSERT_RES, row)
            works += len(norms_batch)
            con.commit()
            print(f"{path}: {works} norms total", flush=True)


def main():
    parser = argparse.ArgumentParser(description="Import ФСНБ XML into norms DB")
    parser.add_argument("--dsn", default=os.environ.get("NORMS_DSN", ""),
                        help="Postgres DSN (or NORMS_DSN env)")
    parser.add_argument("--edition-id", required=True)
    parser.add_argument("--collection", default=None,
                        help="override <base BaseType> (e.g. ГЭСНм)")
    parser.add_argument("files", nargs="+")
    args = parser.parse_args()
    if not args.dsn:
        raise SystemExit("missing --dsn / NORMS_DSN")
    run(args.dsn, args.edition_id, args.files, args.collection)


if __name__ == "__main__":
    main()
