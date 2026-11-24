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
from PIL import Image, ImageChops, ImageFilter, ImageOps
from kac_names import INFO_LETTER, OFFER_NAME, PRICE_LIST, SECTION_NAME


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
STYLES = "word/styles.xml"
DIVIDER = re.compile(rf"^{PRICE_LIST}(\d+)\b", re.I)


def qname(prefix, name):
    return f"{{{NS[prefix]}}}{name}"


def section_offers(folder):
    offers = {}
    for path in folder.iterdir():
        if not path.is_file() or path.suffix.lower() != ".pdf" or INFO_LETTER.match(path.name):
            continue
        offer = OFFER_NAME.match(path.stem)
        if not offer:
            raise ValueError(f"Не найден номер КП в имени «{path.name}».")
        number = tuple(map(int, offer[1].split(".")))
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


def normalize_price_list_appendix(first, titles):
    """Convert manually paginated offer sheets in the working copy to one block per heading."""
    body = first.getparent()
    appendix = list(body)[body.index(first):-1]
    headings = {}
    for paragraph in appendix:
        if paragraph.tag != qname("w", "p"):
            raise ValueError("В приложении КП встретилась таблица или другой отдельный объект.")
        text = paragraph_text(paragraph)
        heading = DIVIDER.match(text)
        if text and not heading:
            raise ValueError("В приложении КП есть текст вне разделителя. Сборка остановлена для его сохранения.")
        # Only replace ordinary picture runs, page breaks and empty paragraphs.
        for child in paragraph:
            if child.tag in {qname("w", tag) for tag in ("pPr", "bookmarkStart", "bookmarkEnd")}:
                continue
            if child.tag != qname("w", "r"):
                raise ValueError("В приложении КП есть неподдерживаемая разметка абзаца.")
            for item in child:
                if item.tag in {qname("w", tag) for tag in ("rPr", "t", "br", "lastRenderedPageBreak")}:
                    continue
                if item.tag == qname("w", "drawing") and item.find(
                    "wp:inline/a:graphic/a:graphicData/{http://schemas.openxmlformats.org/drawingml/2006/picture}pic",
                    NS,
                ) is not None:
                    continue
                raise ValueError("В приложении КП есть объект, который нельзя заменить страницей предложения.")
        if heading:
            number = int(heading[1])
            if number in headings or number not in titles:
                raise ValueError(f"Проверьте разделитель №{number} и соответствующую папку КП.")
            headings[number] = paragraph

    for paragraph in appendix:
        body.remove(paragraph)
    for heading in headings.values():
        for drawing in heading.findall("w:r/w:drawing", NS):
            drawing.getparent().remove(drawing)
        props = heading.find("w:pPr", NS)
        if props is None:
            props = xml.Element(qname("w", "pPr"))
            heading.insert(0, props)
        if props.find("w:sectPr", NS) is None:
            props.append(deepcopy(first.find("w:pPr/w:sectPr", NS)))
        style = first.find("w:pPr/w:pStyle", NS)
        if style is not None and props.find("w:pStyle", NS) is None:
            props.insert(0, deepcopy(style))
        body[-1].addprevious(heading)
        body[-1].addprevious(xml.Element(qname("w", "p")))
    return headings


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
    if tail.tag != qname("w", "sectPr"):
        raise ValueError("В Word отсутствуют завершающие параметры страницы.")
    if list(body)[body.index(first):] != expected:
        dividers = normalize_price_list_appendix(first, titles)
        pairs = {number: (divider, divider.getnext()) for number, divider in dividers.items()}
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
                    with closing(pdf[index]) as page, closing(page.render(scale=350 / 72)) as bitmap:
                        target = png_folder / f"{offer.stem}_стр_{index + 1:03d}.jpg"
                        image = bitmap.to_pil()
                        if orientation_reader and image.height > image.width:
                            rotation = text_rotation(page)
                            if rotation is None:
                                rotation = scan_rotation(image, orientation_reader)
                            if rotation in (90, 270):
                                image = image.rotate(-rotation, expand=True)
                        image.convert("RGB").save(target, quality=95, subsampling=0, dpi=(350, 350))
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


def trim_offer_margins(image, width, height):
    # Keep faint colored stamps and marks by checking every color channel.
    red, green, blue = image.split()
    darkest = ImageChops.darker(ImageChops.darker(red, green), blue)
    if image.width > image.height * 1.10:
        # Neutral scan background can be slightly gray. Keep colored marks
        # and reject isolated dust pixels when estimating the crop.
        lightest = ImageChops.lighter(ImageChops.lighter(red, green), blue)
        color = ImageChops.subtract(lightest, darkest).point(lambda value: 255 if value >= 12 else 0)
        ink = darkest.point(lambda value: 255 if value < 230 else 0)
        mask = ImageChops.lighter(ink, color)
        bounds = mask.filter(ImageFilter.BoxBlur(3)).point(
            lambda value: 255 if value >= 48 else 0).getbbox()
    else:
        bounds = darkest.point(lambda value: 255 if value < 250 else 0).getbbox()
    if bounds is None:
        return image
    left, top, right, bottom = bounds
    padding = round(min(image.size) * 0.02)
    box = (max(0, left - padding), max(0, top - padding),
           min(image.width, right + padding), min(image.height, bottom + padding))
    original_scale = min(width / image.width, height / image.height)
    cropped_scale = min(width / (box[2] - box[0]), height / (box[3] - box[1]))
    if cropped_scale < original_scale * 1.08:
        return image
    return image.crop(box)


def fitted_image(path, extent, extension):
    with Image.open(path) as original:
        landscape_offer = extension == ".jpg" and original.width > original.height * 1.10
        dpi = 350 if extension == ".jpg" else 250
        width = round(int(extent.get("cx")) * dpi / 914400)
        height = round(int(extent.get("cy")) * dpi / 914400)
        contents = original.convert("RGB")
        if extension == ".jpg":
            contents = trim_offer_margins(contents, width, height)
        fitted = ImageOps.contain(contents, (width, height), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (width, height), "white")
        canvas.paste(fitted, ((width - fitted.width) // 2, (height - fitted.height) // 2))
        buffer = io.BytesIO()
        if extension == ".jpg":
            canvas.save(buffer, format="JPEG", quality=97 if landscape_offer else 95, subsampling=0)
        else:
            canvas.save(buffer, format="PNG")
        return buffer.getvalue()


def add_summary_footer(section, relationships, content_types, existing_ids, existing_parts, title):
    part = "kac-summary-footer.xml"
    while f"word/{part}" in existing_parts:
        part = "_" + part
    rid = "rIdKacSummaryFooter"
    while rid in existing_ids:
        rid += "_"
    xml.SubElement(relationships, qname("rel", "Relationship"),
                   Id=rid, Type=f"{NS['r']}/footer", Target=part)
    xml.SubElement(content_types, qname("ct", "Override"),
                   PartName=f"/word/{part}",
                   ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml")
    for ref in section.findall("w:footerReference", NS):
        section.remove(ref)
    section.insert(len(section.findall("w:headerReference", NS)),
                   xml.Element(qname("w", "footerReference"),
                               {qname("w", "type"): "default", qname("r", "id"): rid}))
    footer = xml.fromstring(f'''
        <w:ftr xmlns:w="{NS['w']}"><w:p>
          <w:pPr><w:tabs><w:tab w:val="center" w:pos="11339"/>
            <w:tab w:val="right" w:pos="22394"/></w:tabs>
            <w:spacing w:before="0" w:after="0"/></w:pPr>
          <w:r><w:tab/></w:r>
          <w:r><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/>
            <w:color w:val="000000"/><w:sz w:val="12"/></w:rPr>
            <w:t/></w:r>
          <w:r><w:tab/></w:r>
          <w:fldSimple w:instr=" PAGE \\# &quot;00&quot; ">
            <w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>
              <w:color w:val="000000"/><w:sz w:val="16"/></w:rPr><w:t>00</w:t></w:r>
          </w:fldSimple>
        </w:p></w:ftr>'''.encode())
    footer.find(".//w:r/w:t", NS).text = title
    return f"word/{part}", xml.tostring(footer, encoding="UTF-8", xml_declaration=True)


def blank_summary_header(section, original, following, relationships, content_types,
                         existing_ids, existing_parts):
    part = "kac-summary-header.xml"
    while f"word/{part}" in existing_parts:
        part = "_" + part
    rid = "rIdKacSummaryHeader"
    while rid in existing_ids:
        rid += "_"
    xml.SubElement(relationships, qname("rel", "Relationship"),
                   Id=rid, Type=f"{NS['r']}/header", Target=part)
    xml.SubElement(content_types, qname("ct", "Override"),
                   PartName=f"/word/{part}",
                   ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml")
    for ref in section.findall("w:headerReference", NS):
        section.remove(ref)
    for kind in ("default", "first", "even"):
        section.insert(0, xml.Element(qname("w", "headerReference"),
                       {qname("w", "type"): kind, qname("r", "id"): rid}))
    if following is not None:
        for kind, ref in original.items():
            if following.find(f"w:headerReference[@w:type='{kind}']", NS) is None:
                following.insert(0, deepcopy(ref))
    return f"word/{part}", f'<w:hdr xmlns:w="{NS["w"]}"><w:p/></w:hdr>'.encode()


def insert_summary(document, pages, shape_id, relationships, content_types, existing_ids, existing_parts, title):
    body = document.find("w:body", NS)
    headings = [p for p in body.findall("w:p", NS)
                if paragraph_text(p).casefold() == "сводная таблица результатов конъюнктурного анализа"
                and p.find("w:pPr/w:sectPr", NS) is not None]
    if len(headings) != 1:
        raise ValueError("В DOCX нужен один оформленный раздел «Сводная таблица результатов конъюнктурного анализа».")
    block = headings[0].getnext()
    if not empty_offer_block(block) or block.find("w:pPr/w:sectPr", NS) is None:
        raise ValueError("После заголовка сводной таблицы нужен пустой абзац с разрывом раздела.")
    props = block.find("w:pPr", NS)
    section = props.find("w:sectPr", NS)
    size, _, _ = page_size(section)
    for key, value in (("w", "23811"), ("h", "16838"), ("orient", "landscape"), ("code", "8")):
        size.set(qname("w", key), value)
    margins = section.find("w:pgMar", NS)
    if margins is None:
        margins = xml.SubElement(section, qname("w", "pgMar"))
    for key in ("top", "bottom", "left", "right", "header", "footer", "gutter"):
        margins.set(qname("w", key), "0")
    initial_start_seen = False
    for paragraph in body:
        props_section = paragraph if paragraph.tag == qname("w", "sectPr") else paragraph.find("w:pPr/w:sectPr", NS)
        if props_section is not None:
            numbering = props_section.find("w:pgNumType", NS)
            if numbering is not None and qname("w", "start") in numbering.attrib:
                if initial_start_seen:
                    numbering.attrib.pop(qname("w", "start"))
                initial_start_seen = True
    original_footer = next((ref for p in reversed(list(body)[:body.index(block) + 1])
                            if (ref := p.find("w:pPr/w:sectPr/w:footerReference[@w:type='default']", NS))
                            is not None), None)
    numbering = section.find("w:pgNumType", NS)
    if numbering is None:
        numbering = xml.Element(qname("w", "pgNumType"))
        section.insert(section.index(margins) + 1, numbering)
    numbering.set(qname("w", "fmt"), "decimalZero")
    next_section = next((s for p in list(body)[body.index(block) + 1:]
                         if (s := p.find("w:pPr/w:sectPr", NS)) is not None), None)
    if (original_footer is not None and next_section is not None
            and next_section.find("w:footerReference[@w:type='default']", NS) is None):
        next_section.insert(len(next_section.findall("w:headerReference", NS)), deepcopy(original_footer))
    original_headers = {}
    for preceding in list(body)[:body.index(block) + 1]:
        for ref in preceding.findall("w:pPr/w:sectPr/w:headerReference", NS):
            original_headers[ref.get(qname("w", "type"))] = ref
    for key, value in (("left", "567"), ("right", "850"), ("top", "850"),
                       ("bottom", "850"), ("footer", "455")):
        margins.set(qname("w", key), value)
    props.remove(section)
    template = populate_empty_block(block)[0]
    block.remove(template)
    footer_part, footer_data = add_summary_footer(
        section, relationships, content_types, existing_ids, existing_parts, title)
    images = {footer_part: footer_data}
    header_part, header_data = blank_summary_header(
        section, original_headers, next_section, relationships, content_types, existing_ids, existing_parts)
    images[header_part] = header_data
    paragraph = block
    for number, png in enumerate(pages, 1):
        if number > 1:
            following = xml.Element(qname("w", "p"))
            paragraph.addnext(following)
            paragraph = following
        properties = paragraph.find("w:pPr", NS)
        if properties is None:
            properties = xml.SubElement(paragraph, qname("w", "pPr"))
        if number > 1:
            xml.SubElement(properties, qname("w", "pageBreakBefore"))
        xml.SubElement(properties, qname("w", "spacing"), {
            qname("w", "before"): "0", qname("w", "after"): "0",
        })
        for tag in ("ind", "jc"):
            for node in properties.findall(f"w:{tag}", NS):
                properties.remove(node)
        xml.SubElement(properties, qname("w", "ind"), {
            qname("w", "left"): "0", qname("w", "right"): "0", qname("w", "firstLine"): "0",
        })
        xml.SubElement(properties, qname("w", "jc"), {qname("w", "val"): "left"})
        run = deepcopy(template)
        for extent in run.xpath(".//wp:extent | .//a:xfrm/a:ext", namespaces=NS):
            extent.set("cx", str(22300 * 635))
            extent.set("cy", str(14950 * 635))
        part, data = prepare_image(run, 0, number, shape_id + number, "Сводная таблица", number,
                                   png, relationships, existing_ids, existing_parts)
        run.find(".//wp:docPr", NS).set("descr", f"KAC-SUMMARY:{number}")
        images[part] = data
        paragraph.append(run)
    attach_section(paragraph, section)
    return images


def write_document(source, target, titles, sections, single, summary_pages=(), summary_title=""):
    with ZipFile(source) as archive, ZipFile(target, "w", ZIP_DEFLATED) as output:
        document = xml.fromstring(archive.read(DOCUMENT))
        relationships = xml.fromstring(archive.read(RELATIONSHIPS))
        content_types = xml.fromstring(archive.read(CONTENT_TYPES))
        layout = prepare_layout(document, titles, single)
        existing_ids = {item.get("Id") for item in relationships}
        shape_id = max(int(item.get("id")) for item in document.findall(".//wp:docPr", NS))
        existing_parts = set(archive.namelist())
        images = insert_summary(document, summary_pages, shape_id, relationships, content_types, existing_ids,
                                existing_parts, summary_title) if summary_pages else {}
        shape_id += len(summary_pages)
        for name, data in images.items():
            output.writestr(name, data)
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
                output.writestr(image_part, data)
                block.append(run)
            if linux:
                separate_offer_paragraphs(block, landscape, page_style)

        if not any(item.get("Extension", "").lower() == "png" for item in content_types):
            xml.SubElement(content_types, qname("ct", "Default"),
                           Extension="png", ContentType="image/png")
        if not any(item.get("Extension", "").lower() == "jpg" for item in content_types):
            xml.SubElement(content_types, qname("ct", "Default"),
                           Extension="jpg", ContentType="image/jpeg")
        updated = {DOCUMENT: document, RELATIONSHIPS: relationships, CONTENT_TYPES: content_types}
        if summary_pages and STYLES in existing_parts:
            styles = xml.fromstring(archive.read(STYLES))
            for style in styles.findall("w:style", NS):
                name = style.find("w:name", NS)
                color = style.find("w:rPr/w:color", NS)
                if name is not None and color is not None and (
                    name.get(qname("w", "val"), "").casefold() in {"hyperlink", "followedhyperlink"}
                    or color.get(qname("w", "val")) == "auto"
                ):
                    color.attrib.clear()
                    color.set(qname("w", "val"), "000000")
            updated[STYLES] = styles
        for part in archive.infolist():
            if part.filename in updated:
                data = xml.tostring(updated[part.filename], encoding="UTF-8",
                                    xml_declaration=True, standalone=True)
                output.writestr(part.filename, data)
            else:
                with archive.open(part) as src, output.open(part.filename, "w", force_zip64=part.file_size >= 2**31) as dst:
                    shutil.copyfileobj(src, dst)


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
    already_oriented = (width > height) == landscape
    if already_oriented and not landscape:
        return
    shift = 0 if already_oriented else (height - width) * 635
    inline = run.find("w:drawing/wp:inline", NS)
    extent = inline.find("wp:extent", NS)
    cx = int(extent.get("cx")) + shift
    cy = int(extent.get("cy")) - shift
    if landscape:
        margins = section.find("w:pgMar", NS)
        if margins is not None:
            side_space = sum(int(margins.get(qname("w", side), "0"))
                             for side in ("left", "right", "gutter"))
            cx = max(cx, (max(width, height) - side_space - 80) * 635)
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
    extension = ".jpg" if png.suffix.lower() == ".jpg" else ".png"
    image_part = f"media/kac_{section}_{index}{extension}"
    while relation_id in existing_ids or f"word/{image_part}" in existing_parts:
        relation_id += "_"
        image_part = image_part.removesuffix(extension) + "_" + extension
    xml.SubElement(relationships, qname("rel", "Relationship"),
                   Id=relation_id, Type=f"{NS['r']}/image", Target=image_part)
    inline.find(".//a:blip", NS).set(qname("r", "embed"), relation_id)
    return f"word/{image_part}", fitted_image(png, inline.find("wp:extent", NS), extension)


def blacken_word_headings(docx):
    """Writer can reintroduce theme colors when saving the result as DOCX."""
    fixed = docx.with_suffix(".fixed.docx")
    with ZipFile(docx) as source:
        document = xml.fromstring(source.read(DOCUMENT))
        styles = xml.fromstring(source.read(STYLES))
        heading_ids = set()
        for style in styles.findall("w:style", NS):
            name = style.find("w:name", NS)
            label = name.get(qname("w", "val"), "").casefold() if name is not None else ""
            if (label.startswith(("heading ", "заголовок ", "toc ", "contents "))
                    or label in {"введение", "hyperlink", "followedhyperlink"}
                    or style.find("w:pPr/w:outlineLvl", NS) is not None):
                heading_ids.add(style.get(qname("w", "styleId")))
                set_black_text(style)
        for paragraph in document.findall("w:body/w:p", NS):
            style = paragraph.find("w:pPr/w:pStyle", NS)
            title = paragraph_text(paragraph)
            if ((style is not None and style.get(qname("w", "val")) in heading_ids)
                    or paragraph.find("w:pPr/w:outlineLvl", NS) is not None
                    or (title.isupper() and len(title) <= 300)):
                for run in paragraph.findall(".//w:r", NS):
                    if run.find("w:t", NS) is not None:
                        set_black_text(run)
        updated = {DOCUMENT: document, STYLES: styles}
        for name in source.namelist():
            if re.fullmatch(r"word/footer[^/]*\.xml", name):
                footer = xml.fromstring(source.read(name))
                if set_page_number_font(footer):
                    updated[name] = footer
        with ZipFile(fixed, "w", ZIP_DEFLATED) as target:
            for item in source.infolist():
                node = updated.get(item.filename)
                if node is not None:
                    target.writestr(item, xml.tostring(node, encoding="UTF-8", xml_declaration=True))
                else:
                    with source.open(item) as src, target.open(item.filename, "w", force_zip64=item.file_size >= 2**31) as dst:
                        shutil.copyfileobj(src, dst)
    fixed.replace(docx)


def set_page_number_font(footer):
    runs = []
    for field in footer.findall(".//w:fldSimple", NS):
        if re.match(r"\s*PAGE\b", field.get(qname("w", "instr"), ""), re.I):
            runs.extend(field.findall(".//w:r", NS))
    for paragraph in footer.findall(".//w:p", NS):
        fields = []
        for run in paragraph.findall(".//w:r", NS):
            char = run.find("w:fldChar", NS)
            kind = char.get(qname("w", "fldCharType")) if char is not None else None
            if kind == "begin":
                fields.append(([], []))
            if fields:
                fields[-1][0].append(run)
                fields[-1][1].extend(run.xpath("./w:instrText/text()", namespaces=NS))
                if kind == "end":
                    parts, instruction = fields.pop()
                    if re.match(r"\s*PAGE\b", "".join(instruction), re.I):
                        runs.extend(parts)
    for run in runs:
        props = run.find("w:rPr", NS)
        if props is None:
            props = xml.Element(qname("w", "rPr"))
            run.insert(0, props)
        fonts = props.find("w:rFonts", NS)
        if fonts is None:
            fonts = xml.Element(qname("w", "rFonts"))
            props.insert(0, fonts)
        fonts.attrib.clear()
        for key in ("ascii", "hAnsi", "eastAsia", "cs"):
            fonts.set(qname("w", key), "Times New Roman")
    return bool(runs)


def set_black_text(element):
    props = element.find("w:rPr", NS)
    if props is None:
        props = xml.Element(qname("w", "rPr"))
        if element.tag == qname("w", "r"):
            element.insert(0, props)
        else:
            element.append(props)
    color = props.find("w:color", NS)
    if color is None:
        color = xml.SubElement(props, qname("w", "color"))
    color.attrib.clear()
    color.set(qname("w", "val"), "000000")


def export(docx, pdf, report):
    if sys.platform == "linux":
        subprocess.run([
            "/usr/bin/python3", str(Path(__file__).with_name("export-libreoffice.py")),
            str(docx), str(pdf), str(report.parent),
        ], check=True, timeout=300)
        blacken_word_headings(docx)
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


def tagged_offer_pages(pdf, *, summary=False):
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
            pattern = r"KAC-SUMMARY:(\d+)$" if summary else r"KAC:(\d+):(\d+)\|"
            marker = re.match(pattern, str(node.get("/Alt", "")))
            if marker:
                physical = reader.get_page_number(page)
                if physical is None or physical < 0:
                    raise ValueError("Не удалось определить страницу изображения КП в PDF.")
                section, index = (0, int(marker[1])) if summary else map(int, marker.groups())
                yield {"section": section, "index": index, "physical": physical + 1}
            if "/K" in node:
                yield from visit(node.get("/K"), page)

    return sorted(visit(structure), key=lambda item: (item["physical"], item["section"], item["index"]))


def restore_vector_summary(pdf, summary_pdf):
    """Keep Writer's page references and use Calc's original page contents."""
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import NameObject

    slots = tagged_offer_pages(pdf, summary=True)
    with summary_pdf.open("rb") as source, pdf.open("rb") as original:
        summary = PdfReader(source)
        physical = [slot["physical"] for slot in slots]
        if ([slot["index"] for slot in slots] != list(range(1, len(summary.pages) + 1))
                or len(physical) != len(set(physical))):
            raise ValueError("Не удалось сопоставить страницы сводной таблицы с итоговым PDF.")
        writer = PdfWriter(clone_from=original)
        original.seek(0)
        writer_export = PdfReader(original)
        for slot, sheet in zip(slots, summary.pages, strict=True):
            page = writer.pages[slot["physical"] - 1]
            if any(abs(float(a) - float(b)) > 3 for a, b in zip(page.mediabox, sheet.mediabox)):
                raise ValueError("Размер страницы сводной таблицы в итоговом PDF отличается от A3.")
            page.replace_contents(None)
            page.pop(NameObject("/Annots"), None)
            footer = writer_export.pages[slot["physical"] - 1]
            footer.cropbox.upper_right = (float(page.mediabox.right), 36)
            page.merge_page(sheet)
            page.merge_page(footer)
        with pdf.with_suffix(".vector.pdf").open("wb") as output:
            writer.write(output)
    pdf.with_suffix(".vector.pdf").replace(pdf)


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


def align_summary_tables(pdf, work):
    from pypdf import PdfWriter, Transformation

    bounds = []
    with pdfium.PdfDocument(pdf) as document:
        if not 1 <= len(document) <= 250:
            raise ValueError("Сводная таблица должна занимать от 1 до 250 страниц.")
        for page in document:
            with closing(page):
                width = page.get_width()
                lines = Counter()
                for element in page.get_objects():
                    left, bottom, right, top = element.get_bounds()
                    if right - left > width * 0.65 and top - bottom < 2:
                        lines[round(left, 1), round(right, 1)] += 1
                bounds.append(lines.most_common(1)[0][0] if lines and max(lines.values()) >= 3 else None)
    aligned = work / "aligned-summary.pdf"
    with pdf.open("rb") as source, aligned.open("wb") as target:
        writer = PdfWriter(clone_from=source)
        for page, span in zip(writer.pages, bounds, strict=True):
            if span is None:
                continue
            left, right = span
            desired_left = 10 * 72 / 25.4
            desired_right = float(page.mediabox.width) - 15 * 72 / 25.4
            scale = (desired_right - desired_left) / (right - left)
            if 0.9 <= scale <= 1.15:
                page.add_transformation(Transformation().scale(scale, 1).translate(
                    tx=desired_left - left * scale))
        writer.write(target)
    aligned.replace(pdf)


def render_summary(workbook, work, prepared=None):
    if sys.platform != "linux":
        raise ValueError("Вставка XLSX поддерживается обработчиком КАЦ на Linux с LibreOffice Calc.")
    pdf = work / "summary.pdf"
    subprocess.run([
        "/usr/bin/python3", str(Path(__file__).with_name("export-libreoffice.py")),
        str(workbook), str(pdf), str(work), *([str(prepared)] if prepared else []),
    ], check=True, timeout=300)
    align_summary_tables(pdf, work)
    if prepared:
        # Calc writes explicit heights with customHeight=false. Excel can then
        # recalculate them on open and lose the extra space.
        fixed = work / "fixed-summary.xlsx"
        with ZipFile(workbook) as original, ZipFile(prepared) as source, ZipFile(fixed, "w", ZIP_DEFLATED) as target:
            names = xml.fromstring(source.read("xl/workbook.xml"))
            header_rows = {}
            for name in names.findall(".//{*}definedName"):
                if name.get("name") == "_xlnm.Print_Titles":
                    match = re.search(r"!\$(\d+):\$(\d+)", name.text or "")
                    if match:
                        header_rows[int(name.get("localSheetId", "0")) + 1] = int(match[2])
            for item in source.infolist():
                data = source.read(item)
                if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", item.filename):
                    sheet = xml.fromstring(data)
                    index = int(re.search(r"sheet(\d+)", item.filename)[1])
                    header = header_rows.get(index, 14)
                    original_heights = {}
                    if item.filename in original.namelist():
                        original_sheet = xml.fromstring(original.read(item.filename))
                        original_heights = {row.get("r"): float(row.get("ht"))
                                            for row in original_sheet.findall("./{*}sheetData/{*}row")
                                            if row.get("ht") is not None}
                    for row in sheet.findall("./{*}sheetData/{*}row"):
                        if row.get("ht") is not None:
                            n = int(row.get("r"))
                            if row.get("hidden") not in {"1", "true"} and (n > header or header - 2 <= n < header):
                                height = max(float(row.get("ht")), original_heights.get(str(n), 0))
                                row.set("ht", str(round(min(409, height + (18 if n < header else 9)), 2)))
                            row.set("customHeight", "1")
                    data = xml.tostring(sheet, encoding="UTF-8", xml_declaration=True)
                target.writestr(item, data)
        fixed.replace(prepared)
    pages = []
    with pdfium.PdfDocument(pdf) as document:
        if not 1 <= len(document) <= 250:
            raise ValueError("Сводная таблица должна занимать от 1 до 250 страниц.")
        for index, page in enumerate(document):
            with closing(page), closing(page.render(scale=3, crop=(
                9 * 72 / 25.4, 14 * 72 / 25.4, 14 * 72 / 25.4, 14 * 72 / 25.4,
            ))) as bitmap:
                width, height = page.get_size()
                if abs(width - 1191) > 3 or abs(height - 842) > 3:
                    raise ValueError("Не удалось экспортировать сводную таблицу в альбомном формате A3.")
                png = work / f"summary-{index + 1}.png"
                bitmap.to_pil().save(png)
                pages.append(png)
    return pages


def assemble(source, folder, output, *, approve, workbook=None):
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
        summary_pages = render_summary(workbook, work, result / "summary.xlsx") if workbook else []
        summary_title = (work / "summary-title.txt").read_text(encoding="utf-8") if summary_pages else ""
        write_document(source, docx, titles, sections, single, summary_pages, summary_title)
        print("Обновление оглавления и экспорт PDF…")
        pages = check_pagination(sections, export(docx, pdf, work / "pages.json"))
        if summary_pages:
            restore_vector_summary(pdf, work / "summary.pdf")
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
            writer.writerow(["Раздел", "Файл КП", "Страница КП", "Страница PDF", "Номер на листе", "Изображение"])
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
    parser.add_argument("--xlsx", type=Path, help="Книга сводной таблицы")
    parser.add_argument("-y", "--yes", action="store_true", help="Собрать показанный список без подтверждения")
    args = parser.parse_args()
    try:
        docx = args.docx or Path(input("Путь к основному DOCX: ").strip().strip('"'))
        folder = args.folder or Path(input("Путь к папке прайс-листов или раздела: ").strip().strip('"'))
        output = args.output or Path(input("Путь к новой папке результата: ").strip().strip('"'))
        assemble(docx.resolve(), folder.resolve(), output.resolve(), approve=args.yes,
                 workbook=args.xlsx.resolve() if args.xlsx else None)
    except (OSError, ValueError, subprocess.SubprocessError, EOFError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
