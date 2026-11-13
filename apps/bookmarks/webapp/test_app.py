"""Run: python -m unittest discover -s webapp -p test_app.py -v."""
import io
import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

from pypdf import PdfReader, PdfWriter
from app import create_app


class WebServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="pdf-web-test-", dir=Path(__file__).resolve().parents[1])
        self.app = create_app({"TESTING": True, "DATA_DIR": self.temp.name, "SECRET_KEY": "test-only-secret", "WORKERS": 1})
        self.client = self.app.test_client()

    def tearDown(self):
        state = self.app.extensions["pdf_jobs"]
        state["stop"].set()
        state["pool"].shutdown(wait=True)
        self.temp.cleanup()

    def upload(self, content=b"%PDF-invalid", name="drawing.pdf", **fields):
        response = self.client.post("/api/jobs", data={"file": (io.BytesIO(content), name), **fields}, headers={"X-PDF-Service": "1"})
        response.request.environ["wsgi.input"].close()
        return response

    def wait(self, key):
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            response = self.client.get(f"/api/jobs/{key}")
            data = response.get_json()
            if data["status"] in {"done", "error"}:
                return data
            time.sleep(0.1)
        self.fail("Job did not finish")

    def test_home_and_security_headers(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Графическая часть", response.get_data(as_text=True))
        self.assertIn("frame-ancestors 'none'", response.headers["Content-Security-Policy"])
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        response.close()
        self.assertEqual(self.client.get("/api/health").get_json()["service"], "pdf-bookmarks")
        for asset, content_type in (("style.css", "text/css"), ("app.js", "javascript")):
            asset_response = self.client.get("/static/" + asset)
            self.assertEqual(asset_response.status_code, 200)
            self.assertIn(content_type, asset_response.content_type)
            asset_response.close()
        self.assertEqual(self.client.get("/api/jobs/missing").status_code, 404)

    def test_upload_validation(self):
        self.assertEqual(self.client.post("/api/jobs").status_code, 403)
        self.assertEqual(self.upload(b"not pdf").status_code, 400)
        self.assertEqual(self.upload(name="file.exe").status_code, 400)
        self.assertEqual(self.upload(start="-1").status_code, 400)
        self.assertEqual(self.upload(start="5", end="4").status_code, 400)
        self.assertEqual(self.upload(scale="nan").status_code, 400)
        self.assertEqual(self.upload(scale="inf").status_code, 400)
        self.app.config["MAX_CONTENT_LENGTH"] = 100
        self.assertEqual(self.upload(b"%PDF-" + b"a" * 200).status_code, 413)

    def test_cross_origin_and_queue_limit(self):
        response = self.client.post("/api/jobs", headers={"X-PDF-Service": "1", "Sec-Fetch-Site": "cross-site"})
        self.assertEqual(response.status_code, 403)
        self.app.config["MAX_JOBS"] = 0
        self.assertEqual(self.upload().status_code, 429)

    def test_invalid_pdf_and_session_isolation(self):
        response = self.upload()
        self.assertEqual(response.status_code, 202)
        key = response.get_json()["id"]
        self.assertEqual(self.app.test_client().get(f"/api/jobs/{key}").status_code, 404)
        data = self.wait(key)
        self.assertEqual(data["status"], "error")
        self.assertIn("error", data)
        self.assertEqual(self.client.get(f"/api/jobs/{key}/download/pdf").status_code, 404)
        self.assertFalse((self.app.extensions["pdf_jobs"]["root"] / key / "input.pdf").exists())
        self.app.extensions["pdf_jobs"]["jobs"][key]["finished"] = time.time() - 3601
        self.assertEqual(self.client.get(f"/api/jobs/{key}").status_code, 404)
        self.assertFalse((self.app.extensions["pdf_jobs"]["root"] / key).exists())

    def test_timeout(self):
        with patch("app.subprocess.run", side_effect=subprocess.TimeoutExpired("worker", 300)):
            key = self.upload().get_json()["id"]
            data = self.wait(key)
        self.assertEqual(data["status"], "error")
        self.assertIn("5 минут", data["error"])

    def test_encrypted_and_missing_title_blocks(self):
        for encrypted in (False, True):
            stream = io.BytesIO()
            writer = PdfWriter()
            writer.add_blank_page(width=1191, height=842)
            if encrypted:
                writer.encrypt("test-password")
            writer.write(stream)
            key = self.upload(stream.getvalue()).get_json()["id"]
            data = self.wait(key)
            self.assertEqual(data["status"], "error")
            self.assertIn("защищён паролем" if encrypted else "Чертежи не найдены", data["error"])

    @unittest.skipUnless(os.environ.get("PDF_TEST_FILE"), "Set PDF_TEST_FILE to run the real PDF integration test")
    def test_real_pdf_end_to_end(self):
        source = Path(os.environ["PDF_TEST_FILE"])
        key = self.upload(source.read_bytes(), source.name).get_json()["id"]
        data = self.wait(key)
        self.assertEqual(data["status"], "done", data)
        self.assertEqual(data["added"], 159)
        self.assertEqual(data["pages"], 239)
        other = self.app.test_client()
        self.assertEqual(other.get(f"/api/jobs/{key}/download/pdf").status_code, 404)
        response = self.client.get(f"/api/jobs/{key}/download/pdf")
        self.assertEqual(response.status_code, 200)
        output = PdfReader(io.BytesIO(response.get_data()))
        original = PdfReader(source)
        response.close()
        csv_response = self.client.get(f"/api/jobs/{key}/download/csv")
        self.assertTrue(csv_response.get_data().startswith(b"\xef\xbb\xbf"))
        csv_response.close()
        def find(items, title):
            for index, item in enumerate(items):
                if isinstance(item, list):
                    result = find(item, title)
                    if result:
                        return result
                elif item.title == title:
                    return item, items[index + 1] if index + 1 < len(items) and isinstance(items[index + 1], list) else []
        before = find(original.outline, "")[1]
        after = find(output.outline, "")[1]
        self.assertEqual([(x.title, original.get_destination_page_number(x)) for x in before],
                         [(x.title, output.get_destination_page_number(x)) for x in after if not isinstance(x, list)])
        section, children = find(output.outline, "ГРАФИЧЕСКАЯ ЧАСТЬ")
        self.assertEqual(len(children), 159)
        self.assertEqual(output.get_destination_page_number(section), 78)
        self.assertTrue(all(original.pages[i].get_contents().get_data() == output.pages[i].get_contents().get_data() for i in range(239)))


if __name__ == "__main__":
    unittest.main()
