"""Sequential, retryable file uploads into a private job directory."""
import os
from pathlib import Path
import re
import shutil
import time

from kac_names import SECTION_NAME


WINDOWS_RESERVED = re.compile(r"(?:CON|PRN|AUX|NUL|COM[1-9¹²³]|LPT[1-9¹²³])(?:\.|$)", re.I)


def upload_path(name):
    parts = name.split("/")
    if len(parts) not in (2, 3, 4) or any(
        not part or part in {".", ".."} or part[-1] in ". " or len(part) > 160
        or re.search(r'[<>:"\\|?*\x00-\x1f]', part) or WINDOWS_RESERVED.match(part)
        for part in parts
    ):
        raise ValueError("Проверьте имена папок и файлов КП.")
    folder, filename = parts[-2:]
    section = SECTION_NAME.fullmatch(folder)
    if section is None or not filename.lower().endswith(".pdf"):
        raise ValueError("КП должны лежать в папках разделов.")
    return int(section[1]), folder, filename, "/".join(parts[:-1])


class Upload:
    def __init__(self, folder: Path, owner, count):
        self.folder = folder
        self.owner = owner
        self.count = count
        self.touched = time.time()
        self.next_file = 0
        self.offset = 0
        self.current = None
        self.sections = {}
        self.section_paths = {}
        self.names = set()

    def append(self, index, offset, total, kind, name, stream):
        if min(index, offset, total) < 0 or index >= self.count or offset > total:
            raise ValueError("Неверная позиция файла.")
        if index < self.next_file:
            return  # Response to an already completed file was lost.
        if index != self.next_file:
            raise ValueError("Нарушена последовательность файлов.")
        identity = (kind, name, total)
        if self.current is not None and identity != self.current:
            raise ValueError("Во время загрузки изменился файл.")
        if offset < self.offset:
            return  # Only acknowledged, sequential chunks are retried by the client.
        if offset != self.offset:
            raise ValueError("Пропущена часть файла.")
        if kind == "docx" and index == 0 and name.lower().endswith(".docx"):
            target = self.folder / "source.docx"
        elif kind == "xlsx" and name.lower().endswith(".xlsx"):
            target = self.folder / "summary.xlsx"
            if offset == 0 and target.exists() and self.current is None:
                raise ValueError("Можно загрузить только одну сводную таблицу XLSX.")
        elif kind == "offer":
            section, directory, filename, relative = upload_path(name)
            if self.section_paths.get(section, relative) != relative:
                raise ValueError(f"Загружены две папки для раздела {section}.")
            if (section, filename.casefold()) in self.names:
                raise ValueError(f"В разделе {section} повторяется файл «{filename}».")
            target = self.folder / "offers" / directory / filename
        else:
            raise ValueError("Проверьте тип файла КАЦ.")

        size = stream.seek(0, os.SEEK_END)
        stream.seek(0)
        if offset + size > total or (not size and total):
            raise ValueError("Неверная длина части файла.")
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("r+b" if offset else "wb") as output:
            output.seek(offset)
            shutil.copyfileobj(stream, output)
            output.truncate()
        self.current = identity
        self.offset += size
        if self.offset == total:
            if kind == "offer":
                self.section_paths[section] = relative
                self.sections[section] = directory
                self.names.add((section, filename.casefold()))
            self.next_file += 1
            self.offset = 0
            self.current = None
