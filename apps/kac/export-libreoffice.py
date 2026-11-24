"""Export a prepared DOCX with the Linux LibreOffice UNO runtime."""
from pathlib import Path
import subprocess
import sys
import time
from uuid import uuid4

import uno


def prop(name, value):
    result = uno.createUnoStruct("com.sun.star.beans.PropertyValue")
    result.Name = name
    result.Value = value
    return result


def spreadsheet_title(sheet, area):
    width = area.EndColumn - area.StartColumn + 1
    for row in range(area.StartRow, min(area.EndRow + 1, area.StartRow + 10)):
        for column in range(area.StartColumn, min(area.EndColumn + 1, area.StartColumn + 32)):
            cell = sheet.getCellByPosition(column, row)
            label = " ".join(cell.String.split())
            if not label or len(label) > 200:
                continue
            merge = sheet.createCursorByRange(cell)
            merge.collapseToMergedArea()
            span = merge.getRangeAddress()
            if span.EndColumn - span.StartColumn + 1 >= max(3, width // 2):
                return label
    return ""


def export_spreadsheet(document, pdf, prepared, work):
    styles = document.getStyleFamilies().getByName("PageStyles")
    title = None
    for sheet in document.getSheets():
        if not sheet.IsVisible:
            continue
        style = styles.getByName(sheet.PageStyle)
        style.FooterIsOn = False
        style.TopMargin = 1500
        style.LeftMargin = 1000
        style.RightMargin = 1500
        style.BottomMargin = 1500
        style.IsLandscape = True
        style.Width = 42000
        style.Height = 29700
        style.ScaleToPagesX = 1
        style.ScaleToPagesY = 0
        ranges = sheet.getPrintAreas()
        if not ranges:
            used = sheet.createCursor()
            used.gotoEndOfUsedArea(True)
            ranges = (used.getRangeAddress(),)
        for area in ranges:
            if title is None:
                title = spreadsheet_title(sheet, area)
            header_end = sheet.getTitleRows().EndRow if sheet.getPrintTitleRows() else 13
            start = max(area.StartRow, header_end + 1)
            if start > area.EndRow:
                continue
            rows = sheet.getCellRangeByPosition(0, start, 0, area.EndRow).getRows()
            for row in rows:
                if row.IsVisible:
                    previous = row.Height
                    row.OptimalHeight = True
                    height = max(row.Height, previous) + 250
                    # Persist fixed heights so Excel does not recalculate them on open.
                    row.OptimalHeight = False
                    row.Height = height
    (work / "summary-title.txt").write_text(title or "", encoding="utf-8")
    document.storeToURL(pdf.as_uri(), (prop("FilterName", "calc_pdf_Export"),))
    if prepared is not None:
        document.storeToURL(prepared.as_uri(), (prop("FilterName", "Calc MS Excel 2007 XML"),))


def export(source, pdf, work, prepared=None):
    pipe = f"portal-kac-{uuid4().hex}"
    profile = (work / "office-profile").as_uri()
    process = subprocess.Popen([
        "soffice", f"-env:UserInstallation={profile}", "--headless", "--norestore",
        "--nodefault", f"--accept=pipe,name={pipe};urp;StarOffice.ServiceManager",
    ])
    desktop = document = None
    try:
        local = uno.getComponentContext()
        resolver = local.ServiceManager.createInstanceWithContext(
            "com.sun.star.bridge.UnoUrlResolver", local,
        )
        for _ in range(300):
            try:
                context = resolver.resolve(f"uno:pipe,name={pipe};urp;StarOffice.ComponentContext")
                break
            except uno.getClass("com.sun.star.connection.NoConnectException"):
                if process.poll() is not None:
                    raise RuntimeError("LibreOffice exited during startup")
                time.sleep(0.1)
        else:
            raise RuntimeError("Could not connect to LibreOffice")
        desktop = context.ServiceManager.createInstanceWithContext(
            "com.sun.star.frame.Desktop", context,
        )
        document = desktop.loadComponentFromURL(source.as_uri(), "_blank", 0, (
            prop("Hidden", True),
            prop("MacroExecutionMode", uno.getConstantByName("com.sun.star.document.MacroExecMode.NEVER_EXECUTE")),
            prop("UpdateDocMode", uno.getConstantByName("com.sun.star.document.UpdateDocMode.NO_UPDATE")),
        ))
        if document is None:
            raise RuntimeError("LibreOffice could not open the source document")
        if source.suffix.lower() == ".xlsx":
            export_spreadsheet(document, pdf, prepared, work)
            return
        indexes = document.getDocumentIndexes()
        families = document.getStyleFamilies()
        for family, names in (
            ("CharacterStyles", ("Internet link", "Visited Internet Link", "Index Link")),
            ("ParagraphStyles", tuple(f"Heading {i}" for i in range(1, 11))
             + tuple(f"Contents {i}" for i in range(1, 11)) + ("Contents Heading",)),
        ):
            styles = families.getByName(family)
            for name in names:
                if styles.hasByName(name):
                    styles.getByName(name).CharColor = 0
        for _ in range(2):
            for index in range(indexes.getCount()):
                indexes.getByIndex(index).update()

        document.storeToURL(pdf.as_uri(), (
            prop("FilterName", "writer_pdf_Export"),
            prop("FilterData", uno.Any("[]com.sun.star.beans.PropertyValue", (
                prop("UseTaggedPDF", True),
            ))),
        ))
        document.store()
    finally:
        try:
            if document is not None:
                document.close(True)
            if desktop is not None:
                desktop.terminate()
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=10)


if __name__ == "__main__":
    export(*(Path(value).resolve() for value in sys.argv[1:]))
