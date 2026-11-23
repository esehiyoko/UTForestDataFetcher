import os
import unittest
from unittest.mock import patch

import UTForestDataFetcher


class SkeletonTest(unittest.TestCase):
    def test_weather_module_is_importable(self):
        self.assertTrue(hasattr(UTForestDataFetcher, "Weather"))

    def test_api_origin_is_supplied_at_runtime(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "UTFOREST_API_BASE_URL"):
                UTForestDataFetcher.Weather.api_base_url()
        with patch.dict(os.environ, {"UTFOREST_API_BASE_URL": "https://example.invalid/"}):
            self.assertEqual(
                UTForestDataFetcher.Weather.api_base_url(), "https://example.invalid"
            )


if __name__ == "__main__":
    unittest.main()
