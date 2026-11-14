import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('measurement',Path(__file__).with_name('f6e4-edicion.py'))
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class MeasurementTests(unittest.TestCase):
    def test_http_date_rounding_is_conservative(self):
        value=module.latency_upper_bound('2026-11-13T23:50:00.400Z','Fri, 13 Nov 2026 23:50:01 GMT')
        self.assertAlmostEqual(value,1.6)

    def test_timezone_is_respected(self):
        value=module.latency_upper_bound('2026-11-13T20:50:00-03:00','Fri, 13 Nov 2026 23:50:01 GMT')
        self.assertEqual(value,2)

    def test_threshold_does_not_pass_five_seconds(self):
        value=module.latency_upper_bound('2026-11-13T23:50:00Z','Fri, 13 Nov 2026 23:50:04 GMT')
        self.assertEqual(value,5)
        self.assertFalse(0<=value<5)

    def test_missing_timezone_does_not_assume_a_clock(self):
        with self.assertRaises(ValueError):
            module.latency_upper_bound('2026-11-13T23:50:00','Fri, 13 Nov 2026 23:50:01 GMT')
