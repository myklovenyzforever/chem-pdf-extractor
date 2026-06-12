import unittest
from pathlib import Path

from chem_pdf_extractor.extractor import JobState, state_increment


class JobStateStatisticsTest(unittest.TestCase):
    def test_snapshot_includes_task_statistics_with_zero_defaults(self):
        snapshot = JobState().snapshot()

        self.assertEqual(snapshot["extracted_rows"], 0)
        self.assertEqual(snapshot["suspicious_rows"], 0)
        self.assertEqual(snapshot["bad_rows"], 0)
        self.assertEqual(snapshot["cache_hits"], 0)

    def test_reset_clears_task_statistics(self):
        state = JobState()
        state_increment(state, extracted_rows=3, suspicious_rows=2, bad_rows=1, cache_hits=4)

        state.reset(Path("out.xlsx"), Path("errors.txt"), Path("partial.jsonl"))
        snapshot = state.snapshot()

        self.assertEqual(snapshot["extracted_rows"], 0)
        self.assertEqual(snapshot["suspicious_rows"], 0)
        self.assertEqual(snapshot["bad_rows"], 0)
        self.assertEqual(snapshot["cache_hits"], 0)

    def test_state_increment_updates_task_statistics_only_upward(self):
        state = JobState()

        state_increment(state, extracted_rows=5, suspicious_rows=1, bad_rows=2, cache_hits=3)
        state_increment(state, extracted_rows=0, suspicious_rows=-1, bad_rows=1, cache_hits=2)
        snapshot = state.snapshot()

        self.assertEqual(snapshot["extracted_rows"], 5)
        self.assertEqual(snapshot["suspicious_rows"], 1)
        self.assertEqual(snapshot["bad_rows"], 3)
        self.assertEqual(snapshot["cache_hits"], 5)


if __name__ == "__main__":
    unittest.main()
