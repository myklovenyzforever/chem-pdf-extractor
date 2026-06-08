import csv
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas

from chem_pdf_extractor.config import RuntimeDeps
from chem_pdf_extractor.export import append_jsonl, export_csv, export_excel, write_jsonl
from chem_pdf_extractor.extractor import save_extraction_cache
from chem_pdf_extractor.llm import cloud_chat_completion
from chem_pdf_extractor.pdf import save_markdown_artifacts
from chem_pdf_extractor.server import RequestHandler
from chem_pdf_extractor.text_safety import json_dumps_utf8, utf8_safe_text


def has_surrogate(text: str) -> bool:
    return any(0xD800 <= ord(char) <= 0xDFFF for char in text)


class Utf8SafetyTest(unittest.TestCase):
    def assert_utf8_safe(self, text: str) -> None:
        self.assertFalse(has_surrogate(text))
        text.encode("utf-8")

    def test_utf8_safe_text_replaces_lone_surrogates(self):
        text = "alpha" + chr(0xD800) + "beta" + chr(0xDFFF) + "中文😀"

        cleaned = utf8_safe_text(text)

        self.assert_utf8_safe(cleaned)
        self.assertIn("alpha", cleaned)
        self.assertIn("beta", cleaned)
        self.assertIn("中文😀", cleaned)
        self.assertIn("\uFFFD", cleaned)

    def test_json_dumps_utf8_handles_nested_objects(self):
        payload = {
            "bad" + chr(0xD800): [
                "value" + chr(0xDFFF),
                {"inner": "x" + chr(0xD800)},
            ]
        }

        dumped = json_dumps_utf8(payload)

        self.assert_utf8_safe(dumped)
        loaded = json.loads(dumped)
        self.assertIn("bad\uFFFD", loaded)
        self.assertEqual(loaded["bad\uFFFD"][0], "value\uFFFD")

    def test_append_jsonl_handles_surrogates(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rows.jsonl"

            append_jsonl(path, {"text": "bad" + chr(0xD800)})

            content = path.read_text(encoding="utf-8")
        self.assert_utf8_safe(content)
        self.assertEqual(json.loads(content)["text"], "bad\uFFFD")

    def test_write_jsonl_handles_surrogates(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rows.jsonl"

            write_jsonl(path, [{"text": "bad" + chr(0xD800)}, {"text": "bad" + chr(0xDFFF)}])

            content = path.read_text(encoding="utf-8")
        self.assert_utf8_safe(content)
        self.assertEqual(len([line for line in content.splitlines() if line]), 2)

    def test_save_markdown_artifacts_handles_surrogates(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_dir = Path(tmp)
            pdf_path = input_dir / "paper.pdf"

            markdown_path, _ = save_markdown_artifacts("markdown" + chr(0xD800), pdf_path, input_dir)

            content = markdown_path.read_text(encoding="utf-8")
        self.assert_utf8_safe(content)
        self.assertEqual(content, "markdown\uFFFD")

    def test_save_extraction_cache_handles_surrogates(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache_path = Path(tmp) / "cache" / "paper.json"

            save_extraction_cache(cache_path, [{"field": "value" + chr(0xD800)}])

            content = cache_path.read_text(encoding="utf-8")
        self.assert_utf8_safe(content)
        loaded = json.loads(content)
        self.assertEqual(loaded["rows"][0]["field"], "value\uFFFD")

    def test_cloud_chat_completion_sanitizes_request_body_before_encoding(self):
        captured_data = []

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return b'{"choices":[{"message":{"content":"{}"}}]}'

        def fake_urlopen(request, *args, **kwargs):
            captured_data.append(request.data)
            request.data.decode("utf-8")
            return FakeResponse()

        messages = [{"role": "user", "content": "hello" + chr(0xD800)}]
        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            content = cloud_chat_completion("https://example.invalid/v1", "test-key", "test-model", messages, 5)

        self.assertEqual(content, "{}")
        decoded = captured_data[0].decode("utf-8")
        self.assert_utf8_safe(decoded)
        self.assertIn("hello\uFFFD", decoded)

    def test_send_json_handles_surrogates(self):
        handler = RequestHandler.__new__(RequestHandler)
        handler.wfile = io.BytesIO()
        handler.send_response = lambda status: None
        handler.send_header = lambda key, value: None
        handler.end_headers = lambda: None

        handler.send_json({"message": "bad" + chr(0xD800)})

        content = handler.wfile.getvalue().decode("utf-8")
        self.assert_utf8_safe(content)
        self.assertEqual(json.loads(content)["message"], "bad\uFFFD")

    def test_export_csv_handles_surrogates(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "result.csv"

            export_csv([{"field": "bad" + chr(0xD800)}], output_path)

            content = output_path.read_text(encoding="utf-8-sig")
            with output_path.open("r", encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
        self.assert_utf8_safe(content)
        self.assertEqual(rows[0]["field"], "bad\uFFFD")

    def test_export_excel_handles_surrogates(self):
        runtime = RuntimeDeps(
            pd=pandas,
            PdfReader=None,
            ChatPromptTemplate=None,
            ChatOllama=None,
            Field=None,
            create_model=None,
        )
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "result.xlsx"

            export_excel([{"field": "bad" + chr(0xD800)}], output_path, runtime)

            self.assertTrue(output_path.exists())
            self.assertGreater(output_path.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
