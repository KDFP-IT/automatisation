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


def export(docx, pdf, work):
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
        document = desktop.loadComponentFromURL(docx.as_uri(), "_blank", 0, (
            prop("Hidden", True),
            prop("MacroExecutionMode", uno.getConstantByName("com.sun.star.document.MacroExecMode.NEVER_EXECUTE")),
            prop("UpdateDocMode", uno.getConstantByName("com.sun.star.document.UpdateDocMode.NO_UPDATE")),
        ))
        if document is None:
            raise RuntimeError("LibreOffice could not open DOCX")
        indexes = document.getDocumentIndexes()
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
