from io import BytesIO
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from werkzeug.exceptions import NotFound
from werkzeug.middleware.dispatcher import DispatcherMiddleware

from app import create_kac_app


class UploadTest(unittest.TestCase):
    def setUp(self):
        tmp = self.enterContext(TemporaryDirectory())
        self.root = Path(tmp) / "kac-jobs"
        self.enterContext(patch.dict(os.environ, PDF_WEB_DATA_DIR=tmp, KAC_LOCAL_EXPORT="1"))
        self.enterContext(patch("app.shutil.which", return_value="soffice"))
        app = create_kac_app()
        app.wsgi_app = DispatcherMiddleware(NotFound(), {"/kac": app.wsgi_app})
        service = app.extensions["kac_jobs"]
        self.addCleanup(service["stop"].set)
        self.addCleanup(service["pool"].shutdown)
        self.submit = self.enterContext(patch.object(service["pool"], "submit"))
        self.client = app.test_client()
        self.other = app.test_client()

    def start(self, count):
        response = self.client.post("/kac/api/uploads", json={"files": count})
        self.assertEqual(response.status_code, 201)
        key = response.json["id"]
        self.url = f"/kac/api/uploads/{key}"
        self.folder = self.root / key

    def chunk(self, index, offset, size, kind, name, payload):
        return self.client.post(self.url + "/chunk", data={
            "index": str(index), "offset": str(offset), "total": str(size),
            "kind": kind, "chunk": (BytesIO(payload), name),
        })

    def test_retry_order_ownership_and_idempotent_finish(self):
        self.start(2)
        def doc(offset, payload):
            return self.chunk(0, offset, 6, "docx", "смета.docx", payload)
        self.assertEqual(self.other.post(self.url + "/finish").status_code, 404)
        self.assertEqual(doc(3, b"def").status_code, 400)
        self.assertEqual(doc(0, b"abc").status_code, 200)
        self.assertEqual(doc(0, b"abc").json["offset"], 3)
        self.assertEqual(self.client.post(self.url + "/finish").status_code, 400)
        self.assertEqual(doc(3, b"def").status_code, 200)
        self.assertEqual(doc(3, b"def").status_code, 200)
        self.assertEqual((self.folder / "source.docx").read_bytes(), b"abcdef")
        self.assertEqual(self.chunk(1, 0, 1, "offer", "../КП 1.1.pdf", b"p").status_code, 400)
        self.assertEqual(self.chunk(1, 0, 1, "offer", "Раздел 1 - Сеть/КП 1.1.pdf", b"p").status_code, 200)
        for _ in range(2):
            self.assertEqual(self.client.post(self.url + "/finish").status_code, 202)
        self.submit.assert_called_once()

    def test_more_than_500_offers(self):
        self.start(502)
        self.assertEqual(self.chunk(0, 0, 3, "docx", "смета.docx", b"doc").status_code, 200)
        for i in range(1, 502):
            name = f"Раздел 1 - Сеть/КП 1.{i}.pdf"
            self.assertEqual(self.chunk(i, 0, 1, "offer", name, b"p").status_code, 200)
        self.assertEqual(len(list(self.folder.rglob("*.pdf"))), 501)
        self.assertEqual(self.client.post(self.url + "/finish").status_code, 202)
