import csv
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_DIR = ROOT / "examples" / "benchmark_cases"


SECRET_PATTERNS = [
    re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"\btp-[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"(?i)\b(api[_-]?key|apikey|bearer\s+[A-Za-z0-9_-]+)\b"),
]
PRIVATE_PATH_PATTERNS = [
    re.compile(r"[A-Za-z]:[\\/](?:Users|Documents and Settings)[\\/]", re.IGNORECASE),
    re.compile(r"(?i)\bC:[\\/]Users[\\/]"),
    re.compile(r"/home/[^/\s]+/"),
    re.compile(r"/Users/[^/\s]+/"),
]
COPYRIGHT_REFERENCE_PATTERNS = [
    re.compile(r"(?i)\bcopyrighted\b"),
    re.compile(r"(?i)\bdoi\s*[:/]"),
    re.compile(r"(?i)\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b"),
    re.compile(r"(?i)\.pdf\b"),
]


class BenchmarkCasesTest(unittest.TestCase):
    def case_dirs(self) -> list[Path]:
        self.assertTrue(BENCHMARK_DIR.exists(), "examples/benchmark_cases must exist")
        return sorted(path for path in BENCHMARK_DIR.iterdir() if path.is_dir())

    def read_case_text(self, case_dir: Path) -> str:
        pieces = []
        for path in sorted(case_dir.iterdir()):
            if path.is_file() and path.suffix.lower() in {".md", ".txt", ".json", ".csv"}:
                pieces.append(path.read_text(encoding="utf-8"))
        return "\n".join(pieces)

    def test_required_case_categories_exist(self):
        names = {path.name for path in self.case_dirs()}

        self.assertGreaterEqual(len(names), 4)
        for expected in [
            "catalysis_reaction_conditions",
            "materials_synthesis",
            "environmental_treatment",
            "electrochemistry",
        ]:
            self.assertIn(expected, names)

    def test_each_case_has_required_files_and_valid_fields(self):
        for case_dir in self.case_dirs():
            with self.subTest(case=case_dir.name):
                self.assertTrue((case_dir / "README.md").exists())
                self.assertTrue((case_dir / "input.md").exists() or (case_dir / "input.txt").exists())
                self.assertTrue((case_dir / "fields.json").exists())
                self.assertTrue((case_dir / "golden_output.csv").exists())

                fields = json.loads((case_dir / "fields.json").read_text(encoding="utf-8"))
                self.assertIsInstance(fields, list)
                self.assertGreaterEqual(len(fields), 3)
                for field in fields:
                    self.assertIsInstance(field, dict)
                    self.assertIsInstance(field.get("label"), str)
                    self.assertTrue(field["label"].strip())
                    self.assertIn(field.get("requirement"), {"required", "recommended", "optional"})
                    self.assertIsInstance(field.get("description"), str)
                    self.assertTrue(field["description"].strip())

    def test_golden_output_has_expected_headers_and_rows(self):
        for case_dir in self.case_dirs():
            with self.subTest(case=case_dir.name):
                fields = json.loads((case_dir / "fields.json").read_text(encoding="utf-8"))
                labels = [item["label"] for item in fields]
                with (case_dir / "golden_output.csv").open("r", encoding="utf-8", newline="") as handle:
                    reader = csv.DictReader(handle)
                    rows = list(reader)

                self.assertIsNotNone(reader.fieldnames)
                self.assertGreaterEqual(len(rows), 1)
                for label in labels:
                    self.assertIn(label, reader.fieldnames)
                for row in rows:
                    self.assertTrue(any(str(value or "").strip() for value in row.values()))

    def test_case_text_declares_synthetic_or_public_safe(self):
        for case_dir in self.case_dirs():
            with self.subTest(case=case_dir.name):
                readme = (case_dir / "README.md").read_text(encoding="utf-8").lower()
                input_path = case_dir / "input.md" if (case_dir / "input.md").exists() else case_dir / "input.txt"
                input_text = input_path.read_text(encoding="utf-8").lower()

                self.assertTrue("synthetic" in readme or "public-safe" in readme)
                self.assertTrue("synthetic" in input_text or "public-safe" in input_text)
                self.assertRegex(input_text, r"not copied from a\s+real paper")

    def test_case_text_has_no_secrets_private_paths_or_copyrighted_references(self):
        for case_dir in self.case_dirs():
            text = self.read_case_text(case_dir)
            with self.subTest(case=case_dir.name):
                for pattern in SECRET_PATTERNS:
                    self.assertIsNone(pattern.search(text), pattern.pattern)
                for pattern in PRIVATE_PATH_PATTERNS:
                    self.assertIsNone(pattern.search(text), pattern.pattern)
                for pattern in COPYRIGHT_REFERENCE_PATTERNS:
                    self.assertIsNone(pattern.search(text), pattern.pattern)


if __name__ == "__main__":
    unittest.main()
