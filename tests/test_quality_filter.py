import unittest

from chem_pdf_extractor.quality import calculate_fill_rate, row_is_bad_data


class QualityFilterTest(unittest.TestCase):
    def setUp(self):
        self.fields = [
            {"label": "paper_title", "requirement": "required", "description": "Title"},
            {"label": "catalyst", "requirement": "required", "description": "Catalyst"},
            {"label": "temperature_c", "requirement": "recommended", "description": "Temperature"},
            {"label": "notes", "requirement": "optional", "description": "Notes"},
        ]

    def test_fill_rate_counts_weighted_required_fields(self):
        row = {"paper_title": "Demo", "catalyst": "Ni/Al2O3", "temperature_c": "", "notes": ""}
        rate = calculate_fill_rate(row, self.fields)
        self.assertGreater(rate, 0.5)
        self.assertLess(rate, 1.0)

    def test_low_fill_rate_row_is_bad_data(self):
        row = {"paper_title": "", "catalyst": "", "temperature_c": "", "notes": ""}
        self.assertTrue(row_is_bad_data(row, self.fields, min_fill_rate=0.4))

    def test_good_row_is_not_bad_data(self):
        row = {"paper_title": "Demo", "catalyst": "Cu-ZnO", "temperature_c": 260, "notes": ""}
        self.assertFalse(row_is_bad_data(row, self.fields, min_fill_rate=0.4))


if __name__ == "__main__":
    unittest.main()
