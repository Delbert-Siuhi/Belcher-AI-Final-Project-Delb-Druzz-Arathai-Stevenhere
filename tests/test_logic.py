import unittest

from piflow.logic import EventFilter, MonitorConfig, summarize
from piflow.models import Detection


class LogicTests(unittest.TestCase):
    def test_summary_single(self):
        self.assertEqual(summarize([Detection(label="person", confidence=0.9)]), "Detected a person.")

    def test_summary_multiple(self):
        message = summarize([
            Detection(label="person", confidence=0.9),
            Detection(label="person", confidence=0.8),
            Detection(label="backpack", confidence=0.7),
        ])
        self.assertEqual(message, "Detected a backpack and 2 persons.")

    def test_event_filter_confidence_and_watchlist(self):
        filt = EventFilter(MonitorConfig(min_confidence=0.8, cooldown_seconds=0, watch_labels={"person"}))
        low = filt.make_event([Detection(label="person", confidence=0.5)])
        self.assertIsNone(low)
        event = filt.make_event([Detection(label="person", confidence=0.9)])
        self.assertIsNotNone(event)
        self.assertEqual(event.message, "Detected a person.")

    def test_event_filter_cooldown(self):
        filt = EventFilter(MonitorConfig(min_confidence=0.5, cooldown_seconds=999, watch_labels={"person"}))
        first = filt.make_event([Detection(label="person", confidence=0.9)])
        second = filt.make_event([Detection(label="person", confidence=0.9)])
        self.assertIsNotNone(first)
        self.assertIsNone(second)


if __name__ == "__main__":
    unittest.main()
