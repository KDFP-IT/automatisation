"""PDF processing in a separate process: PDFium is not shared across threads."""
from __future__ import annotations

import csv
from dataclasses import asdict
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pypdf import PdfReader
from add_drawing_bookmarks import scan, write_pdf


def process(folder: Path):
    options = json.loads((folder / "options.json").read_text(encoding="utf-8"))
    source = folder / "input.pdf"
    reader = PdfReader(source)
    if reader.is_encrypted:
        raise ValueError("PDF защищён паролем. Загрузите копию без защиты.")
    pages = len(reader.pages)
    if pages > options["max_pages"]:
        raise ValueError(f"В PDF больше {options['max_pages']} страниц. Разделите документ.")
    drawings, problems = scan(source, options["start"], options["end"], options["scale"])
    if not drawings:
        raise ValueError("Чертежи не найдены. Нужен PDF с текстовым слоем и стандартным штампом 185 × 55 мм. Для скана сначала выполните OCR.")
    if problems and not options["allow_incomplete"]:
        details = "; ".join(f"стр. {page}: {fields}" for page, fields in problems[:10])
        raise ValueError("Есть неполные штампы: " + details + ". Проверьте PDF или разрешите пропуск в параметрах.")
    added = write_pdf(source, folder / "result.pdf", drawings)
    with (folder / "bookmarks.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(asdict(drawings[0])), delimiter=";")
        writer.writeheader()
        writer.writerows(asdict(drawing) for drawing in drawings)
    return {"pages": pages, "added": added,
            "warnings": [f"Страница {page}: пропущен неполный штамп ({fields})" for page, fields in problems],
            "drawings": [asdict(drawing) for drawing in drawings]}


if __name__ == "__main__":
    job_folder = Path(sys.argv[1])
    try:
        result = {"ok": True, **process(job_folder)}
    except ValueError as error:
        result = {"ok": False, "error": str(error)}
    except Exception:
        import traceback
        traceback.print_exc()
        result = {"ok": False, "error": "Не удалось прочитать или обработать PDF. Проверьте файл и повторите попытку. Если ошибка повторится, обратитесь к администратору."}
    (job_folder / "details.json").write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
