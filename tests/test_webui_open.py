import io
import sys
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from chem_pdf_extractor import app as app_module
from chem_pdf_extractor import server as server_module


class FakeServer:
    def __init__(self, address, handler):
        self.address = address
        self.handler = handler
        self.closed = False

    def serve_forever(self):
        return None

    def server_close(self):
        self.closed = True


class WebUiOpenTest(unittest.TestCase):
    def run_start_web_app(self, *, open_browser):
        with (
            patch("chem_pdf_extractor.config.ensure_dependencies"),
            patch("chem_pdf_extractor.config.import_runtime_dependencies", return_value=object()),
            patch.object(server_module, "find_free_port", return_value=8766),
            patch.object(server_module, "ThreadingHTTPServer", FakeServer),
            patch.object(server_module.webbrowser, "open") as open_mock,
            redirect_stdout(io.StringIO()) as output,
        ):
            result = server_module.start_web_app(8766, auto_install=False, open_browser=open_browser)
        return result, open_mock, output.getvalue()

    def test_start_web_app_does_not_open_browser_by_default(self):
        result, open_mock, output = self.run_start_web_app(open_browser=False)

        self.assertEqual(result, 0)
        open_mock.assert_not_called()
        self.assertIn("Chem-PDF-Extractor 页面已启动：", output)
        self.assertIn("http://127.0.0.1:8766/", output)
        self.assertIn("请复制上面的地址到浏览器打开。", output)

    def test_start_web_app_opens_browser_when_requested(self):
        result, open_mock, output = self.run_start_web_app(open_browser=True)

        self.assertEqual(result, 0)
        open_mock.assert_called_once_with("http://127.0.0.1:8766/")
        self.assertIn("Chem-PDF-Extractor 页面已启动：", output)

    def test_parse_args_supports_open_browser_flag(self):
        with patch.object(sys, "argv", ["prog", "--open-browser"]):
            args = app_module.parse_args()

        self.assertTrue(args.open_browser)

    def test_main_passes_open_browser_to_web_app(self):
        with (
            patch.object(sys, "argv", ["prog", "--open-browser"]),
            patch("chem_pdf_extractor.server.start_web_app", return_value=0) as start_mock,
        ):
            result = app_module.main()

        self.assertEqual(result, 0)
        start_mock.assert_called_once_with(8766, auto_install=True, open_browser=True)


if __name__ == "__main__":
    unittest.main()
