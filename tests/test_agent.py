import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from hiver_agent import classify, run_agent  # noqa: E402


class AgentTests(unittest.TestCase):
    def test_security_case_escalates(self):
        result = run_agent("I think my Apple ID was hacked", [])
        self.assertEqual(result.intent, "privacy_or_security")
        self.assertTrue(result.escalate)

    def test_delivery_case_is_classified(self):
        intent, confidence, evidence = classify("Where is my package tracking update?")
        self.assertEqual(intent, "delivery_or_order")
        self.assertGreater(confidence, 0.6)
        self.assertIn("package", evidence)

    def test_unknown_case_escalates(self):
        result = run_agent("Can someone help with this unusual issue?", [])
        self.assertTrue(result.escalate)
        self.assertTrue(result.escalation_reason)
