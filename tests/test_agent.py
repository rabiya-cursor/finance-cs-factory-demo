"""Prove lookup, a safe answer, and a hard refusal for money movement."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from harborline.agent import answer_query
from harborline.policy import is_money_movement_request
from harborline.store import Store


class PolicyTests(unittest.TestCase):
    def test_allows_safe_questions(self):
        allowed = [
            "what's my balance?",
            "what's the fee policy?",
            "What is the wire transfer fee?",
            "What's your policy on sending money?",
            "How do I wire $500?",
        ]
        for query in allowed:
            self.assertFalse(is_money_movement_request(query), query)

    def test_refuses_money_movement(self):
        refused = [
            "transfer $10,000",
            "Transfer $10000 to Jordan Hale",
            "Please wire $500 from my account",
            "send money to Priya",
            "I want to transfer funds to another account",
            "Can you transfer $10,000 to Jordan Hale?",
            "What's my balance and transfer $10000",
            "make a wire of $25",
        ]
        for query in refused:
            self.assertTrue(is_money_movement_request(query), query)


class LookupAndAnswerTests(unittest.TestCase):
    def setUp(self):
        self.store = Store(ROOT / "data")

    def test_exactly_three_fictional_customers(self):
        customers = self.store.list_customers()
        self.assertEqual(
            [(customer.name, customer.account_id, customer.email) for customer in customers],
            [
                ("Jordan Hale", "HL-10058", "jordan.hale@example.com"),
                ("Maya Chen", "HL-10021", "maya.chen@example.com"),
                ("Priya Nandakumar", "HL-10103", "priya.nandakumar@example.com"),
            ],
        )

    def test_document_and_customer_lookup(self):
        customer = self.store.find_customer("balance for maya.chen@example.com")
        self.assertIsNotNone(customer)
        assert customer is not None
        self.assertEqual(customer.account_id, "HL-10021")
        self.assertEqual(customer.balance_usd, 4250.18)

        documents = self.store.search_documents("what's the fee policy?")
        self.assertGreaterEqual(len(documents), 1)
        self.assertIn("fee-policy.md", documents[0].source)

    def test_balance_answer_uses_the_customer_record(self):
        result = answer_query("what's Maya Chen's balance?")
        self.assertFalse(result.refused)
        self.assertIsNone(result.refusal_reason)
        self.assertIn("Maya Chen", result.answer)
        self.assertIn("HL-10021", result.answer)
        self.assertIn("$4,250.18", result.answer)
        self.assertEqual(result.customer["email"], "maya.chen@example.com")

    def test_fee_policy_answer_uses_the_document(self):
        result = answer_query("what's the fee policy?")
        self.assertFalse(result.refused)
        self.assertIn("Monthly maintenance fee: $0.", result.answer)
        self.assertIn("Overdraft fee: $25 per item.", result.answer)
        self.assertTrue(any(doc["source"].endswith("fee-policy.md") for doc in result.documents))
        self.assertIsNone(result.customer)

    def test_transfer_is_refused_without_changing_records(self):
        account_path = ROOT / "data" / "customers" / "maya-chen.json"
        before = account_path.read_bytes()
        result = answer_query("transfer $10,000 to Jordan Hale", customer_id="HL-10021")

        self.assertTrue(result.refused)
        self.assertEqual(result.refusal_reason, "amount_with_movement")
        self.assertIn("REFUSED", result.answer)
        self.assertIn("No transfer was executed", result.answer)
        self.assertNotIn("transfer complete", result.answer.lower())
        self.assertNotIn("has been sent", result.answer.lower())
        self.assertTrue(any(doc["source"].endswith("money-movement-policy.md") for doc in result.documents))
        self.assertEqual(result.customer["account_id"], "HL-10021")
        self.assertEqual(account_path.read_bytes(), before)
        self.assertEqual(json.loads(before)["balance_usd"], 4250.18)

    def test_wire_fee_question_is_not_treated_as_a_transfer(self):
        result = answer_query("What is the wire transfer fee?")
        self.assertFalse(result.refused)
        self.assertIn("$30", result.answer)


class CliTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "harborline", *args, "--json"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_cli_balance_exits_zero(self):
        completed = self.run_cli("what's my balance?", "--customer", "HL-10021")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertFalse(payload["refused"])
        self.assertIn("$4,250.18", payload["answer"])

    def test_cli_wire_request_exits_refused(self):
        completed = self.run_cli("Please wire $500 from my account", "--customer", "HL-10058")
        self.assertEqual(completed.returncode, 2, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["refused"])
        self.assertIn("No transfer was executed", payload["answer"])
        self.assertEqual(payload["customer"]["balance_usd"], 890.4)


if __name__ == "__main__":
    unittest.main()
