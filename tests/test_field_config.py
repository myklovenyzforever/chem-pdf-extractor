import unittest

from chem_pdf_extractor.config import normalize_fields, normalize_requirement
from chem_pdf_extractor.quality import field_weight


class FieldConfigTest(unittest.TestCase):
    def test_normalize_fields_adds_type_and_requirement(self):
        fields = normalize_fields(
            [
                {"label": "temperature_c", "requirement": "required", "description": "Temperature in Celsius"},
                {"label": "notes", "requirement": "free", "description": "Any notes"},
            ]
        )
        self.assertEqual(fields[0]["requirement"], "required")
        self.assertIn(fields[0]["type"], {"float", "str"})
        self.assertEqual(fields[1]["requirement"], "optional")

    def test_requirement_aliases(self):
        self.assertEqual(normalize_requirement("必填"), "required")
        self.assertEqual(normalize_requirement("建议"), "recommended")
        self.assertEqual(normalize_requirement("选填"), "optional")
        self.assertEqual(normalize_requirement("unknown"), "optional")

    def test_requirement_weights(self):
        self.assertGreater(field_weight({"requirement": "required"}), field_weight({"requirement": "recommended"}))
        self.assertGreater(field_weight({"requirement": "recommended"}), field_weight({"requirement": "optional"}))


if __name__ == "__main__":
    unittest.main()
