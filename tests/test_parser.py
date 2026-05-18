import unittest

from piflow.parser import parse_line, normalize_score


class ParserTests(unittest.TestCase):
    def test_key_value_format(self):
        detections = parse_line("label=person confidence=0.91")
        self.assertEqual(len(detections), 1)
        self.assertEqual(detections[0].label, "person")
        self.assertAlmostEqual(detections[0].confidence, 0.91)

    def test_percent_format(self):
        detections = parse_line("person confidence: 91%")
        self.assertEqual(len(detections), 1)
        self.assertEqual(detections[0].label, "person")
        self.assertAlmostEqual(detections[0].confidence, 0.91)

    def test_json_detections(self):
        detections = parse_line('{"detections":[{"label":"cell phone","confidence":0.83}]}')
        self.assertEqual(len(detections), 1)
        self.assertEqual(detections[0].label, "cell phone")
        self.assertAlmostEqual(detections[0].confidence, 0.83)

    def test_allowed_labels(self):
        detections = parse_line("person confidence: 91%", allowed_labels={"dog"})
        self.assertEqual(detections, [])

    def test_score_normalization(self):
        self.assertEqual(normalize_score(91), 0.91)
        self.assertEqual(normalize_score(0.91), 0.91)
        self.assertIsNone(normalize_score(101))


if __name__ == "__main__":
    unittest.main()
