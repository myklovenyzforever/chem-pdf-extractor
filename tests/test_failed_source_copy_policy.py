import tempfile
import unittest
from pathlib import Path

from chem_pdf_extractor.config import FAILED_SOURCES_DIR_NAME
from chem_pdf_extractor.extractor import record_failure


class FailedSourceCopyPolicyTest(unittest.TestCase):
    def test_record_failure_does_not_copy_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pdf = root / "paper.pdf"
            pdf.write_bytes(b"%PDF-1.4")
            error_log = root / "errors.txt"

            record_failure(
                error_log_path=error_log,
                pdf_path=pdf,
                input_dir=root,
                stage="test",
                exc=RuntimeError("boom"),
                copy_failed_sources=False,
            )

            self.assertTrue(error_log.exists())
            self.assertFalse((root / FAILED_SOURCES_DIR_NAME).exists())

    def test_record_failure_copies_when_enabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pdf = root / "paper.pdf"
            pdf.write_bytes(b"%PDF-1.4")
            error_log = root / "errors.txt"

            record_failure(
                error_log_path=error_log,
                pdf_path=pdf,
                input_dir=root,
                stage="test",
                exc=RuntimeError("boom"),
                copy_failed_sources=True,
            )

            self.assertTrue((root / FAILED_SOURCES_DIR_NAME / "paper.pdf").exists())


if __name__ == "__main__":
    unittest.main()
