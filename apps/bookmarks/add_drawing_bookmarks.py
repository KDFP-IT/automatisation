"""Replace automatic sheet bookmarks while preserving document sections."""
from __future__ import annotations

import argparse
from contextlib import closing
import csv
import os
from pathlib import Path
import re
import sys
import tempfile
from dataclasses import dataclass, asdict

import pypdfium2 as pdfium
from pypdf import PdfReader, PdfWriter
from pypdf.generic import DictionaryObject


# Points measured from the right and bottom edges of the visible page.
# Standard 185 x 55 mm title block, with a 5 mm right/bottom margin.
BOXES = {
    "code": (355, 141, 14, 170),
    "name": (355, 57, 157, 100),
    "process": (355, 14, 157, 57),
    "sheet": (115, 57, 72, 85),
}
CODE_RE = re.compile(r"[\w]+(?:\s*[/.-]\s*[\w]+)+", re.UNICODE)
SHEET_RE = re.compile(r"\d+(?:[.,]\d+)?[а-яА-Яa-zA-Z]?")


@dataclass
class Drawing:
    page: int
    sheet: str
    code: str
    name: str
    process: str
    title: str


def clean(text: str) -> str:
    # Some CAD exports encode an ordinary hyphen as U+0002.
    text = text.replace("\x02", "-").replace("\u00ad", "")
    text = re.sub(r"-\s*\r?\n\s*", "-", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_box(page, textpage, box, scale: float) -> str:
    left, bottom, right, top = (n * scale for n in box)
    width = page.get_width()
    x0, x1, y0, y1 = width - left, width - right, bottom, top
    bx0, by0, bx1, by1 = page.get_bbox()
    raw_width, raw_height = bx1 - bx0, by1 - by0
    rotation = page.get_rotation()

    def inverse(x, y):
        if rotation == 0:
            return bx0 + x, by0 + y
        if rotation == 90:
            return bx0 + raw_width - y, by0 + x
        if rotation == 180:
            return bx0 + raw_width - x, by0 + raw_height - y
        if rotation == 270:
            return bx0 + y, by0 + raw_height - x
        raise ValueError(f"Неожиданный поворот страницы: {rotation}")

    corners = [inverse(x, y) for x in (x0, x1) for y in (y0, y1)]
    xs, ys = zip(*corners)
    return clean(textpage.get_text_bounded(min(xs), min(ys), max(xs), max(ys)))


def scan(source: Path, start: int, end: int | None, scale: float):
    drawings, problems = [], []
    with pdfium.PdfDocument(str(source)) as doc:
        last = len(doc) if end is None else end
        if not 1 <= start <= last <= len(doc):
            raise ValueError(f"Диапазон страниц должен быть внутри 1..{len(doc)}")
        for index in range(start - 1, last):
            with closing(doc[index]) as page:
                if page.get_width() < 355 * scale or page.get_height() < 170 * scale:
                    continue
                with closing(page.get_textpage()) as textpage:
                    fields = {key: extract_box(page, textpage, box, scale)
                              for key, box in BOXES.items()}
                    stage = extract_box(page, textpage, (157, 57, 115, 85), scale)
                # Only a complete code in the code cell identifies a title block.
                if not CODE_RE.fullmatch(fields["code"]) or stage not in {"П", "Р", "РП", "P"}:
                    continue
                fields["code"] = re.sub(r"\s*([/.-])\s*", r"\1", fields["code"])
                missing = [key for key in ("sheet", "name", "process") if not fields[key]]
                if not SHEET_RE.fullmatch(fields["sheet"]):
                    missing.append("sheet (некорректный номер)")
                if missing:
                    problems.append((index + 1, ", ".join(missing)))
                    continue
                name = fields["name"].rstrip(". ")
                title = (f"Лист {fields['sheet']} {fields['code']} "
                         f"{name}. {fields['process']}")
                drawings.append(Drawing(index + 1, title=title, **fields))
            if (index + 1) % 25 == 0:
                print(f"Проверено страниц: {index + 1}/{last}", flush=True)
    return drawings, problems


def outline_keys(reader):
    result = set()

    def visit(items):
        for item in items:
            if isinstance(item, list):
                visit(item)
            else:
                try:
                    page = reader.get_destination_page_number(item)
                except (ValueError, KeyError, TypeError):
                    page = None
                result.add((str(item.get("/Title", "")), page))
    visit(reader.outline)
    return result


def write_pdf(source: Path, output: Path, drawings: list[Drawing]) -> int:
    if source.resolve() == output.resolve():
        raise ValueError("Выходной файл должен отличаться от исходного")
    if output.exists():
        raise FileExistsError(f"Файл уже существует: {output}")
    reader = PdfReader(source)
    if reader.is_encrypted:
        raise ValueError("Зашифрованный PDF не поддерживается")
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)
    if not drawings:
        raise ValueError("Нет чертежей для создания раздела «Графическая часть»")
    def snapshot(parent):
        if hasattr(parent, "get_object"):
            parent = parent.get_object()
        nodes = []
        ref = parent.get("/First")
        while ref is not None:
            node = ref.get_object()
            nodes.append((node, snapshot(node)))
            ref = node.get("/Next")
        return nodes

    def has_sheet_views(children):
        return any(clean(str(node.get("/Title", ""))).casefold() == "листы и виды"
                   or has_sheet_views(nested) for node, nested in children)

    def is_automatic(node, children):
        title = clean(str(node.get("/Title", "")))
        if title.casefold() == "листы и виды":
            return True
        if has_sheet_views(children) and (re.fullmatch(r"\d+(?:[-.]\d+)?", title)
                                          or title.lower().endswith(".pdf")):
            return True
        # Replace our previously generated entries as well when reprocessing.
        if re.match(r"^Лист \d+(?:[.,]\d+)?[а-яА-Яa-zA-Z]? \S+ ", title):
            return True
        return False

    old_nodes = snapshot(writer.root_object.get("/Outlines", {}))
    writer.root_object.pop("/Outlines", None)
    section = None

    def restore(nodes, parent=None):
        nonlocal section
        for node, children in nodes:
            if is_automatic(node, children):
                continue
            fields = DictionaryObject({key: value for key, value in node.items()
                                       if str(key) not in {"/Parent", "/Prev", "/Next", "/First", "/Last", "/Count"}})
            saved = writer.add_outline_item_dict(fields, parent=parent,
                                                 is_open=int(node.get("/Count", 0)) >= 0)
            if clean(str(node.get("/Title", ""))).casefold() == "графическая часть":
                if section is not None:
                    raise ValueError("Найдено несколько разделов «Графическая часть»")
                section = saved
            restore(children, saved)

    restore(old_nodes)
    if section is None:
        section = writer.add_outline_item("Графическая часть", drawings[0].page - 1)
    # Capture all preserved titles and destinations before appending drawings.
    preserved_keys = outline_keys(writer)
    expected = set()
    count = 0
    for drawing in drawings:
        key = (drawing.title, drawing.page - 1)
        if key in expected:
            continue
        writer.add_outline_item(drawing.title, drawing.page - 1, parent=section)
        expected.add(key)
        count += 1
    writer.page_mode = "/UseOutlines"
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(suffix=".pdf", dir=output.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            writer.write(stream)
        check = PdfReader(temporary)
        if (len(check.pages) != len(reader.pages)
                or expected | preserved_keys != outline_keys(check)):
            raise RuntimeError("Проверка сохранённых страниц и закладок не пройдена")
        # Do not overwrite an existing destination, including one created during writing.
        with open(temporary, "rb") as src, output.open("xb") as dst:
            import shutil
            shutil.copyfileobj(src, dst)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return count


def main(argv=None):
    parser = argparse.ArgumentParser(description=(
        "Удаляет автоматические закладки листов, сохраняет разделы и создаёт ссылки вида: Лист 79 30/09-ИЛО.КР "
        "Здание решеток. Армирование стен внутри раздела «Графическая часть». "
        "Данные берутся из стандартного штампа."))
    parser.add_argument("input", type=Path, help="Исходный PDF")
    parser.add_argument("-o", "--output", type=Path, help="Новый PDF")
    parser.add_argument("--start-page", type=int, default=1, help="Первая страница PDF (с 1)")
    parser.add_argument("--end-page", type=int, help="Последняя страница PDF включительно")
    parser.add_argument("--stamp-scale", type=float, default=1, help="Масштаб штампа (обычно 1)")
    parser.add_argument("--dry-run", action="store_true", help="Показать список без записи PDF")
    parser.add_argument("--report", type=Path, help="Записать распознанные данные в CSV UTF-8 BOM")
    parser.add_argument("--allow-incomplete", action="store_true", help="Пропустить неполные штампы")
    args = parser.parse_args(argv)
    if args.stamp_scale <= 0:
        parser.error("--stamp-scale должен быть положительным")
    output = args.output or args.input.with_name(args.input.stem + "_с_закладками.pdf")
    if args.report and args.report.resolve() in (args.input.resolve(), output.resolve()):
        parser.error("Путь CSV должен отличаться от путей PDF")
    drawings, problems = scan(args.input, args.start_page, args.end_page, args.stamp_scale)
    for drawing in drawings:
        print(f"PDF {drawing.page}: {drawing.title}")
    for page, problem in problems:
        print(f"ВНИМАНИЕ: PDF {page}: не распознаны поля: {problem}", file=sys.stderr)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        with args.report.open("x", newline="", encoding="utf-8-sig") as stream:
            csv_writer = csv.DictWriter(stream, fieldnames=list(Drawing.__dataclass_fields__), delimiter=";")
            csv_writer.writeheader()
            csv_writer.writerows(asdict(d) for d in drawings)
    if not drawings:
        raise ValueError("Штампы не найдены. Для сканов требуется OCR; другой шаблон штампа требует настройки BOXES.")
    if problems and not args.allow_incomplete:
        raise ValueError("Есть неполные штампы. Проверьте список; PDF не записан. Для пропуска: --allow-incomplete")
    print(f"Найдено чертежей: {len(drawings)}; неполных штампов: {len(problems)}")
    if not args.dry_run:
        count = write_pdf(args.input, output, drawings)
        print(f"Добавлено закладок: {count}\nСохранено: {output}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        sys.exit(1)
