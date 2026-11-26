from email.header import decode_header, make_header
from pathlib import Path
import os
import unittest
from unittest.mock import patch


with patch.dict(os.environ, {
    "SESSION_SECRET": "local-test", "AUTH_MODE": "local",
    "LOCAL_LOGIN": "test", "LOCAL_PASSWORD": "test",
    "ACCESS_FILE": str(Path(__file__).resolve().parents[2] / "deploy/portal/access/access.toml"),
}):
    from server import display_header


class DisplayHeaderTest(unittest.TestCase):
    def test_names_fit_one_http_line_and_decode_for_audit(self):
        for name in ("", "Alex Smith", "André", "Иван Иванов", "Александров Александр Александрович"):
            with self.subTest(name=name):
                header = display_header(name)
                self.assertNotIn("\n", header)
                self.assertNotIn("\r", header)
                self.assertEqual(str(make_header(decode_header(header))), name)
                if name.isascii():
                    self.assertEqual(header, name)
