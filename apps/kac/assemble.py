"""Assemble commercial offers in a copy of a KAC Word document."""

import argparse
import csv
import io
import json
import math
import re
import shutil
import subprocess
import sys
from collections import Counter
from contextlib import closing
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile

import pypdfium2 as pdfium
from lxml import etree as xml
from PIL import Image, ImageOps


NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "wp14": "http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
    "ct": "http://schemas.openxmlformats.org/package/2006/content-types",
}
DOCUMENT = "word/document.xml"
RELATIONSHIPS = "word/_rels/document.xml.rels"
CONTENT_TYPES = "[Content_Types].xml"
OFFER_NAME = re.compile(r"^КП\s*(\d+)\s*\.\s*(\d+)(?![\d.])", re.IGNORECASE)
DIVIDER = re.compile(r"^ПРАЙС[-–‑]ЛИСТЫ\s+К\s+РАЗДЕЛУ\s+КАЦ\s*№\s*(\d+)\b", re.IGNORECASE)
SECTION_NAME = re.compile(r"^Раздел\s+(\d+)\s*[-–—]\s*(\S.*)$", re.IGNORECASE)


def qname(prefix, name):
    return f"{{{NS[prefix]}}}{name}"


def section_offers(folder):
    offers = {}
    for path in folder.iterdir():
        if not path.is_file() or path.suffix.lower() != ".pdf":
            continue
        offer = OFFER_NAME.match(path.stem)
        if not offer:
            raise ValueError(f"Не найден номер КП в имени «{path.name}».")
        number = tuple(map(int, offer.groups()))
        if number in offers:
            raise ValueError(f"Одинаковые номера КП: «{offers[number].name}» и «{path.name}».")
        offers[number] = path
    return [offers[number] for number in sorted(offers)]


def find_sections(folder):
    single = SECTION_NAME.fullmatch(folder.name) is not None
    candidates = [folder] if single else sorted(folder.iterdir())
    sections = {}
    empty = []
    for path in candidates:
        if not path.is_dir() or not (match := SECTION_NAME.fullmatch(path.name)):
            continue
        number, title = int(match[1]), match[2]
        if number in sections or number in empty:
            raise ValueError(f"Две папки с номером раздела {number}.")
        offers = section_offers(path)
        if offers:
            sections[number] = (title, offers)
        else:
            empty.append(number)
    if not sections:
        raise ValueError(f"В «{folder}» нет разделов с PDF.")
    return single, dict(sorted(sections.items())), sorted(empty)


def paragraph_text(paragraph):
    return "".join(paragraph.xpath(".//w:t/text()", namespaces=NS)).strip()


def find_dividers(document):
    body = document.find("w:body", NS)
    dividers = {}
    for paragraph in body.findall("w:p", NS):
        divider = DIVIDER.match(paragraph_text(paragraph))
        if divider and paragraph.find("w:pPr/w:sectPr", NS) is not None:
            section = int(divider[1])
            if section in dividers:
                raise ValueError(f"В Word два разделителя прайс-листов №{section}.")
            dividers[section] = paragraph
    return dividers


def block_runs(block):
    if block is None or block.tag != qname("w", "p") or paragraph_text(block):
        raise ValueError("После разделителя ожидается абзац с изображениями КП.")
    runs = block.findall("w:r", NS)
    if not runs or any(
        run.find("w:drawing/wp:inline", NS) is None
        or any(child.tag not in {qname("w", tag) for tag in ("rPr", "lastRenderedPageBreak", "drawing")}
               for child in run)
        for run in runs
    ) or any(child.tag not in {qname("w", "r"), qname("w", "pPr")} for child in block):
        raise ValueError("Блок КП должен содержать только встроенные изображения.")
    return runs


def empty_offer_block(block):
    """Only accept empty paragraphs, never text, drawings or other content."""
    if block is None or block.tag != qname("w", "p"):
        return False
    for child in block:
        if child.tag == qname("w", "pPr"):
            continue
        if child.tag != qname("w", "r"):
            return False
        for item in child:
            if item.tag == qname("w", "rPr"):
                continue
            if item.tag != qname("w", "t") or (item.text or "").strip():
                return False
    return True


def populate_empty_block(block):
    for child in list(block):
        if child.tag == qname("w", "r"):
            block.remove(child)
    run = xml.fromstring(
        '<w:r xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
        'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        '<w:drawing><wp:inline><wp:extent cx="6120000" cy="7920000"/>'
        '<wp:docPr id="1" name="KAC template"/>'
        '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        '<pic:pic><pic:nvPicPr><pic:cNvPr id="0" name="KAC"/><pic:cNvPicPr/></pic:nvPicPr>'
        '<pic:blipFill><a:blip/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
        '<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="6120000" cy="7920000"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
        '</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r>'
    )
    block.append(run)
    return [run]


def new_divider(template, section, title):
    divider = deepcopy(template)
    run = deepcopy(divider.find("w:r", NS))
    for child in list(divider)[1:]:
        divider.remove(child)
    for marker in run.findall("w:lastRenderedPageBreak", NS):
        run.remove(marker)
    run.find("w:t", NS).text = f"ПРАЙС-ЛИСТЫ К РАЗДЕЛУ КАЦ №{section}–{title.upper()}"
    divider.append(run)
    return divider


def continue_duplicate_numbering(divider):
    numbering = divider.find("w:pPr/w:sectPr/w:pgNumType", NS)
    start = qname("w", "start")
    if numbering is None or start not in numbering.attrib:
        return
    previous = divider.xpath(
        "preceding-sibling::w:p[w:pPr/w:sectPr][1]/w:pPr/w:sectPr/w:pgNumType",
        namespaces=NS,
    )
    if previous and previous[0].get(start) == numbering.get(start):
        del numbering.attrib[start]


def prepare_layout(document, titles, single):
    dividers = find_dividers(document)
    if single:
        number = next(iter(titles))
        if number not in dividers:
            raise ValueError(f"В Word нет разделителя прайс-листов №{number}.")
        divider = dividers[number]
        if divider is next(iter(dividers.values())):
            continue_duplicate_numbering(divider)
        block = divider.getnext()
        runs = populate_empty_block(block) if empty_offer_block(block) else block_runs(block)
        return {number: (block, runs)}
    if not dividers:
        raise ValueError("В Word нужен хотя бы один оформленный разделитель прайс-листов.")
    missing = sorted(dividers.keys() - titles.keys())
    if missing:
        raise ValueError(f"Для существующих блоков Word нет исходных PDF в разделах {missing}.")
    body = document.find("w:body", NS)
    tail = body[-1]
    first = next(iter(dividers.values()))
    pairs = {number: (divider, divider.getnext()) for number, divider in dividers.items()}
    expected = [node for pair in pairs.values() for node in pair] + [tail]
    if tail.tag != qname("w", "sectPr") or list(body)[body.index(first):] != expected:
        raise ValueError("После первого разделителя ожидаются только пары «разделитель и страницы КП».")
    continue_duplicate_numbering(first)
    first_section = first.find("w:pPr/w:sectPr", NS)
    initial_numbering = deepcopy(first_section.find("w:pgNumType", NS))
    template_block = first.getnext()
    existing_runs = {}
    empty = [number for number, (_, block) in pairs.items() if empty_offer_block(block)]
    if empty and len(empty) != len(pairs):
        raise ValueError("Пустые блоки КП нельзя смешивать с оформленными блоками.")
    for number, (divider, block) in pairs.items():
        existing_runs[number] = populate_empty_block(block) if empty else block_runs(block)
        body.remove(divider)
        body.remove(block)

    layout = {}
    final_section = None
    for position, (number, title) in enumerate(titles.items()):
        if number in pairs:
            divider, block = pairs[number]
            runs = existing_runs[number]
        else:
            divider = new_divider(first, number, title)
            block = deepcopy(template_block)
            runs = block_runs(block)
        props = divider.find("w:pPr/w:sectPr", NS)
        numbering = props.find("w:pgNumType", NS)
        if numbering is not None:
            numbering.attrib.pop(qname("w", "start"), None)
        elif position == 0 and initial_numbering is not None:
            numbering = deepcopy(initial_numbering)
            cols = props.find("w:cols", NS)
            props.insert(props.index(cols) if cols is not None else len(props), numbering)
        if position == 0 and initial_numbering is not None:
            start = initial_numbering.get(qname("w", "start"))
            if start is not None:
                numbering.set(qname("w", "start"), start)

        block_props = block.find("w:pPr", NS)
        if block_props is None:
            block_props = xml.Element(qname("w", "pPr"))
            block.insert(0, block_props)
        section_props = block_props.find("w:sectPr", NS)
        if section_props is None:
            section_props = deepcopy(tail)
            block_props.append(section_props)
        final_section = section_props
        body.insert(len(body) - 1, divider)
        body.insert(len(body) - 1, block)
        layout[number] = (block, runs)

    final_section.getparent().remove(final_section)
    body.replace(tail, final_section)
    return layout


def render_offers(offers, png_folder):
    png_folder.mkdir()
    orientation_reader = shutil.which("tesseract") if sys.platform == "linux" else None
    rows = []
    for offer in offers:
        try:
            with pdfium.PdfDocument(offer) as pdf:
                if not len(pdf):
                    raise ValueError("нет страниц")
                for index in range(len(pdf)):
                    with closing(pdf[index]) as page, closing(page.render(scale=250 / 72)) as bitmap:
                        target = png_folder / f"{offer.stem}_стр_{index + 1:03d}.png"
                        image = bitmap.to_pil()
                        if orientation_reader and image.height > image.width:
                            rotation = text_rotation(page)
                            if rotation is None:
                                rotation = scan_rotation(image, orientation_reader)
                            if rotation in (90, 270):
                                image = image.rotate(-rotation, expand=True)
                        image.save(target, dpi=(250, 250))
                    rows.append((offer.name, index + 1, target))
        except Exception as error:
            raise ValueError(f"Не удалось подготовить «{offer.name}»: {error}") from error
    return rows


def text_rotation(page):
    angles = Counter()
    page_rotation = page.get_rotation()
    with closing(page.get_textpage()) as text:
        for index in range(text.count_chars()):
            codepoint = pdfium.raw.FPDFText_GetUnicode(text, index)
            if 0 < codepoint <= 0x10FFFF and chr(codepoint).isalnum():
                angle = pdfium.raw.FPDFText_GetCharAngle(text, index)
                if angle >= 0:
                    quarter_turn = round(math.degrees(angle) / 90) * 90
                    angles[(quarter_turn - page_rotation) % 360] += 1
    if angles:
        rotation, count = angles.most_common(1)[0]
        if count >= 40 and count >= 0.9 * angles.total():
            return rotation
    return None


def tesseract_result(image, executable, language, mode, *options):
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    try:
        result = subprocess.run(
            [executable, "stdin", "stdout", "-l", language, "--psm", mode, "--dpi", "150", *options],
            input=buffer.getvalue(), capture_output=True, timeout=12,
        )
    except (OSError, subprocess.TimeoutExpired):
        return b""
    return result.stdout if result.returncode == 0 else b""


def recognition_score(image, executable):
    result = tesseract_result(image, executable, "rus+eng", "11", "tsv")
    score = 0
    for line in result.decode("utf-8", errors="replace").splitlines():
        fields = line.split("\t", 11)
        if len(fields) == 12 and fields[0] == "5" and float(fields[10]) >= 60:
            score += sum(char.isalnum() for char in fields[11])
    return score


def scan_rotation(image, executable):
    sample = ImageOps.grayscale(image)
    sample.thumbnail((1500, 1500))
    osd = tesseract_result(sample, executable, "osd", "0")
    rotation = re.search(rb"(?m)^Rotate: (0|90|180|270)$", osd)
    confidence = re.search(rb"(?m)^Orientation confidence: ([0-9.]+)$", osd)
    if rotation and confidence and float(confidence[1]) >= 12:
        return int(rotation[1])
    # Weak orientation scores on scanned tables are common. Confirm a turn
    # only when the text is substantially clearer in one of the two directions.
    if rotation and confidence and int(rotation[1]) not in (90, 270) and float(confidence[1]) >= 5:
        return 0
    upright = recognition_score(sample, executable)
    clockwise = recognition_score(sample.rotate(-90, expand=True), executable)
    counterclockwise = recognition_score(sample.rotate(90, expand=True), executable)
    best = max(clockwise, counterclockwise)
    if best >= max(45, upright * 2.5, min(clockwise, counterclockwise) * 1.25):
        return 90 if clockwise > counterclockwise else 270
    return 0


def fitted_png(path, extent):
    width = round(int(extent.get("cx")) * 250 / 914400)
    height = round(int(extent.get("cy")) * 250 / 914400)
    with Image.open(path) as original:
        fitted = ImageOps.contain(original.convert("RGB"), (width, height), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (width, height), "white")
        canvas.paste(fitted, ((width - fitted.width) // 2, (height - fitted.height) // 2))
        buffer = io.BytesIO()
        canvas.save(buffer, format="PNG")
        return buffer.getvalue()


def write_document(source, target, titles, sections, single):
    with ZipFile(source) as archive:
        document = xml.fromstring(archive.read(DOCUMENT))
        relationships = xml.fromstring(archive.read(RELATIONSHIPS))
        content_types = xml.fromstring(archive.read(CONTENT_TYPES))
        layout = prepare_layout(document, titles, single)
        existing_ids = {item.get("Id") for item in relationships}
        shape_id = max(int(item.get("id")) for item in document.findall(".//wp:docPr", NS))
        existing_parts = set(archive.namelist())
        images = {}
        for section, rows in sections.items():
            block, old_runs = layout[section]
            linux = sys.platform == "linux"
            landscape = []
            page_style = offer_section(block) if linux else None
            for run in old_runs:
                block.remove(run)
            for index, (offer, page, png) in enumerate(rows, start=1):
                shape_id += 1
                run = deepcopy(old_runs[min(index, len(old_runs)) - 1])
                if linux:
                    with Image.open(png) as image:
                        wide = image.width > image.height * 1.10
                    landscape.append(wide)
                    resize_offer_extent(run, page_style, wide)
                image_part, data = prepare_image(
                    run, section, index, shape_id, offer, page, png,
                    relationships, existing_ids, existing_parts,
                )
                images[image_part] = data
                block.append(run)
            if linux:
                separate_offer_paragraphs(block, landscape, page_style)

        if not any(item.get("Extension", "").lower() == "png" for item in content_types):
            xml.SubElement(content_types, qname("ct", "Default"),
                           Extension="png", ContentType="image/png")
        updated = {DOCUMENT: document, RELATIONSHIPS: relationships, CONTENT_TYPES: content_types}
        with ZipFile(target, "w", ZIP_DEFLATED) as output:
            for part in archive.infolist():
                data = (xml.tostring(updated[part.filename], encoding="UTF-8", xml_declaration=True,
                                     standalone=True)
                        if part.filename in updated else archive.read(part))
                output.writestr(part.filename, data)
            for name, data in images.items():
                output.writestr(name, data)


def offer_section(block):
    section = block.find("w:pPr/w:sectPr", NS)
    if section is not None:
        return section
    following = block.getnext()
    if following is not None and following.tag == qname("w", "sectPr"):
        return following
    raise ValueError("В шаблоне не заданы параметры страницы КП.")


def page_size(section):
    size = section.find("w:pgSz", NS)
    if size is None:
        raise ValueError("В шаблоне не задан размер страницы КП.")
    return size, int(size.get(qname("w", "w"))), int(size.get(qname("w", "h")))


def resize_offer_extent(run, section, landscape):
    _, width, height = page_size(section)
    if (width > height) == landscape:
        return
    shift = (height - width) * 635
    inline = run.find("w:drawing/wp:inline", NS)
    extent = inline.find("wp:extent", NS)
    cx = int(extent.get("cx")) + shift
    cy = int(extent.get("cy")) - shift
    if min(cx, cy) <= 0:
        raise ValueError("Поля шаблона не оставляют места для изображения в выбранной ориентации.")
    for size in [extent, *inline.findall(".//a:xfrm/a:ext", NS)]:
        size.set("cx", str(cx))
        size.set("cy", str(cy))


def oriented_section(template, landscape, continuation):
    section = deepcopy(template)
    size, width, height = page_size(section)
    if (width > height) != landscape:
        size.set(qname("w", "w"), str(height))
        size.set(qname("w", "h"), str(width))
        size.set(qname("w", "orient"), "landscape" if landscape else "portrait")
    if continuation:
        kind = section.find("w:type", NS)
        if kind is None:
            kind = xml.Element(qname("w", "type"))
            section.insert(section.index(size), kind)
        kind.set(qname("w", "val"), "nextPage")
        numbering = section.find("w:pgNumType", NS)
        if numbering is not None:
            numbering.attrib.pop(qname("w", "start"), None)
    return section


def separate_offer_paragraphs(block, landscape, section):
    """Give Writer separate pages and split the section when orientation changes."""
    runs = block.findall("w:r", NS)
    properties = block.find("w:pPr", NS)
    tail = section.getparent() is block.getparent()
    if not tail:
        properties.remove(section)
    base_props = deepcopy(properties) if properties is not None else xml.Element(qname("w", "pPr"))
    previous = block
    continuation = False
    for index, run in enumerate(runs[1:], start=1):
        paragraph = xml.Element(qname("w", "p"))
        props = deepcopy(base_props)
        page_break = props.find("w:pageBreakBefore", NS)
        if landscape[index] != landscape[index - 1]:
            attach_section(previous, oriented_section(section, landscape[index - 1], continuation))
            continuation = True
            if page_break is not None:
                props.remove(page_break)
        else:
            if page_break is None:
                page_break = xml.Element(qname("w", "pageBreakBefore"))
                preceding = {qname("w", key) for key in ("pStyle", "keepNext", "keepLines")}
                props.insert(sum(child.tag in preceding for child in props), page_break)
            page_break.set(qname("w", "val"), "1")
        paragraph.append(props)
        paragraph.append(run)
        previous.addnext(paragraph)
        previous = paragraph
    final = oriented_section(section, landscape[-1], continuation)
    if tail:
        section.getparent().replace(section, final)
    else:
        attach_section(previous, final)


def attach_section(paragraph, section):
    props = paragraph.find("w:pPr", NS)
    if props is None:
        props = xml.Element(qname("w", "pPr"))
        paragraph.insert(0, props)
    props.append(section)


def prepare_image(run, section, index, shape_id, offer, page, png,
                  relationships, existing_ids, existing_parts):
    for marker in run.findall("w:lastRenderedPageBreak", NS):
        run.remove(marker)
    inline = run.find("w:drawing/wp:inline", NS)
    for attribute in ("anchorId", "editId"):
        inline.attrib.pop(qname("wp14", attribute), None)
    shape = inline.find("wp:docPr", NS)
    shape.set("id", str(shape_id))
    shape.set("name", f"КАЦ {section} — {index}")
    shape.set("descr", f"KAC:{section}:{index}|{offer} — стр. {page}")
    for crop in inline.findall(".//a:srcRect", NS):
        crop.getparent().remove(crop)
    relation_id = f"rIdKac{section}_{index}"
    image_part = f"media/kac_{section}_{index}.png"
    while relation_id in existing_ids or f"word/{image_part}" in existing_parts:
        relation_id += "_"
        image_part = image_part.removesuffix(".png") + "_.png"
    xml.SubElement(relationships, qname("rel", "Relationship"),
                   Id=relation_id, Type=f"{NS['r']}/image", Target=image_part)
    inline.find(".//a:blip", NS).set(qname("r", "embed"), relation_id)
    return f"word/{image_part}", fitted_png(png, inline.find("wp:extent", NS))


def export(docx, pdf, report):
    if sys.platform == "linux":
        subprocess.run([
            "/usr/bin/python3", str(Path(__file__).with_name("export-libreoffice.py")),
            str(docx), str(pdf), str(report.parent),
        ], check=True, timeout=300)
        pages = tagged_offer_pages(pdf)
        with pdfium.PdfDocument(pdf) as exported:
            for item in pages:
                with closing(exported[item["physical"] - 1]) as page, closing(page.get_textpage()) as text:
                    footer = text.get_text_bounded(
                        left=page.get_width() * 0.55, bottom=0, right=page.get_width(), top=58,
                    )
                numbers = re.findall(r"(?m)^\s*(\d+)\s*$", footer)
                if len(numbers) != 1:
                    raise ValueError(f"Не найден однозначный номер на листе PDF {item['physical']}.")
                item["printed"] = int(numbers[0])
        return pages
    command = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "RemoteSigned", "-File",
               str(Path(__file__).with_name("export-word.ps1")),
               "-Docx", str(docx), "-Pdf", str(pdf), "-Report", str(report)]
    subprocess.run(command, check=True)
    return json.loads(report.read_text(encoding="utf-8-sig"))


def tagged_offer_pages(pdf):
    from pypdf import PdfReader
    from pypdf.generic import ArrayObject, DictionaryObject

    reader = PdfReader(pdf)
    structure = reader.root_object.get("/StructTreeRoot")
    if structure is None:
        raise ValueError("В PDF отсутствуют метки страниц КП.")

    def visit(ref, page=None):
        node = ref.get_object()
        if isinstance(node, ArrayObject):
            for child in node:
                yield from visit(child, page)
        elif isinstance(node, DictionaryObject):
            page = node.get("/Pg", page)
            marker = re.match(r"KAC:(\d+):(\d+)\|", str(node.get("/Alt", "")))
            if marker:
                physical = reader.get_page_number(page)
                if physical is None or physical < 0:
                    raise ValueError("Не удалось определить страницу изображения КП в PDF.")
                section, index = map(int, marker.groups())
                yield {"section": section, "index": index, "physical": physical + 1}
            if "/K" in node:
                yield from visit(node.get("/K"), page)

    return sorted(visit(structure), key=lambda item: (item["physical"], item["section"], item["index"]))


def check_pagination(sections, report):
    pages = [page for page in report if page["section"] in sections]
    expected = [(number, index) for number, rows in sections.items()
                for index in range(1, len(rows) + 1)]
    actual = [(page["section"], page["index"]) for page in pages]
    if actual != expected:
        mismatch = next(((wanted, found) for wanted, found in zip(expected, actual)
                         if wanted != found), None)
        detail = f" Первое расхождение (раздел, лист КП): {mismatch[0]} → {mismatch[1]}." if mismatch else ""
        raise ValueError(f"Страницы КП не соответствуют списку исходников: "
                         f"ожидалось {len(expected)}, найдено {len(actual)}.{detail}")
    for current, following in zip(pages, pages[1:]):
        step = 1 if following["section"] == current["section"] else 2
        if any(following[key] - current[key] != step for key in ("physical", "printed")):
            raise ValueError(
                f"Нарушен порядок листов у раздела {following['section']}. "
                f"Страницы PDF {current['physical']} → {following['physical']}, "
                f"номера листов {current['printed']} → {following['printed']}."
            )
    return pages


def assemble(source, folder, output, *, approve):
    if source.suffix.lower() != ".docx" or not source.is_file():
        raise ValueError("Укажите существующий основной файл DOCX.")
    single, source_sections, empty = find_sections(folder)
    titles = {number: title for number, (title, _) in source_sections.items()}
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise ValueError(f"Папка результата уже существует: {output}")
    with ZipFile(source) as archive:
        prepare_layout(xml.fromstring(archive.read(DOCUMENT)), titles, single)
    with TemporaryDirectory(dir=output.parent, prefix=".kac-") as temporary:
        work = Path(temporary)
        result = work / "result"
        result.mkdir()
        sections = {}
        png_root = result / "Картинки"
        png_root.mkdir()
        for section, (_, offers) in source_sections.items():
            png_folder = png_root / f"Раздел {section}"
            rows = render_offers(offers, png_folder)
            sections[section] = rows
            print(f"Раздел {section} — {len(offers)} КП, {len(rows)} стр.")
            for offer in offers:
                print(f"  {offer.name}")
        if empty:
            print(f"Разделы без PDF: {', '.join(map(str, empty))}.")
        if not approve and input("Собрать этот список? [д/н] ").strip().lower() not in {"д", "да", "y"}:
            return
        name = f"КАЦ — раздел {next(iter(sections))}" if single else "КАЦ — полный комплект"
        docx = result / f"{name}.docx"
        pdf = docx.with_suffix(".pdf")
        write_document(source, docx, titles, sections, single)
        print("Обновление оглавления и экспорт PDF…")
        pages = check_pagination(sections, export(docx, pdf, work / "pages.json"))
        rows = [row for section_rows in sections.values() for row in section_rows]
        with pdfium.PdfDocument(pdf) as exported:
            if len(exported) < pages[-1]["physical"]:
                raise ValueError("В PDF отсутствуют страницы из отчёта экспорта.")
            if sys.platform == "linux":
                for (_, _, png), item in zip(rows, pages, strict=True):
                    with Image.open(png) as image, closing(exported[item["physical"] - 1]) as page:
                        if (image.width > image.height * 1.10) != (page.get_width() > page.get_height()):
                            raise ValueError(f"Неверная ориентация страницы PDF {item['physical']}.")
        with (result / "Страницы КП.csv").open("w", newline="", encoding="utf-8-sig") as stream:
            writer = csv.writer(stream, delimiter=";")
            writer.writerow(["Раздел", "Файл КП", "Страница КП", "Страница PDF", "Номер на листе", "PNG"])
            for (offer, number, image), page in zip(rows, pages, strict=True):
                writer.writerow([page["section"], offer, number, page["physical"],
                                 page["printed"], str(image.relative_to(result))])
        result.rename(output)
    print(f"Готово: {output}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("docx", type=Path, nargs="?")
    parser.add_argument("folder", type=Path, nargs="?", help="Папка прайс-листов или одного раздела")
    parser.add_argument("-o", "--output", type=Path, help="Новая папка результата")
    parser.add_argument("-y", "--yes", action="store_true", help="Собрать показанный список без подтверждения")
    args = parser.parse_args()
    try:
        docx = args.docx or Path(input("Путь к основному DOCX: ").strip().strip('"'))
        folder = args.folder or Path(input("Путь к папке прайс-листов или раздела: ").strip().strip('"'))
        output = args.output or Path(input("Путь к новой папке результата: ").strip().strip('"'))
        assemble(docx.resolve(), folder.resolve(), output.resolve(), approve=args.yes)
    except (OSError, ValueError, subprocess.SubprocessError, EOFError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
