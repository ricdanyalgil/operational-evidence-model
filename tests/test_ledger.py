import json
import tempfile
import unittest
from pathlib import Path

from oem.canonical import CanonicalError, canonical_bytes
from oem.keys import Signer, TrustStore
from oem.ledger import Ledger, LedgerCorrupt, merkle_root, verify


class LedgerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.signer = Signer.generate()
        self.trust = TrustStore({self.signer.key_id: TrustStore.entry(self.signer, "t", "t")})
        self.ledger = Ledger(self.tmp / "l.jsonl")
        for i in range(5):
            self.ledger.append("event", {"i": i}, self.signer)

    def lines(self):
        return self.ledger.path.read_text().splitlines()

    def write(self, lines):
        self.ledger.path.write_text("\n".join(lines) + "\n")

    def test_clean_ledger_verifies(self):
        self.assertTrue(verify(self.ledger.records(), self.trust).ok)

    def test_edit_is_caught_at_that_record(self):
        lines = self.lines()
        rec = json.loads(lines[2]); rec["body"]["i"] = 99
        lines[2] = json.dumps(rec)
        self.write(lines)
        report = verify(self.ledger.records(), self.trust)
        self.assertFalse(report.ok)
        self.assertIn("seq 2", report.failures[0])

    def test_delete_swap_and_insert_are_caught(self):
        original = self.lines()
        for mutated in (
            original[:2] + original[3:],                       # delete
            original[:1] + [original[2], original[1]] + original[3:],  # swap
            original[:3] + [original[3]] + original[3:],       # duplicate/insert
        ):
            self.write(mutated)
            self.assertFalse(verify(self.ledger.records(), self.trust).ok)

    def test_untrusted_key_is_rejected(self):
        other = TrustStore({})
        self.assertFalse(verify(self.ledger.records(), other).ok)

    def test_rechain_with_trusted_key_needs_checkpoint(self):
        checkpoint = self.ledger.checkpoint()
        forged = Ledger(self.tmp / "forged.jsonl")
        for i in range(5):
            forged.append("event", {"i": i if i != 3 else 42}, self.signer)
        self.assertTrue(verify(forged.records(), self.trust).ok)            # chain alone: blind
        self.assertFalse(verify(forged.records(), self.trust, checkpoint).ok)

    def test_tail_truncation_needs_checkpoint(self):
        checkpoint = self.ledger.checkpoint()
        self.write(self.lines()[:-2])
        self.assertTrue(verify(self.ledger.records(), self.trust).ok)
        self.assertFalse(verify(self.ledger.records(), self.trust, checkpoint).ok)

    def test_appending_after_checkpoint_still_verifies(self):
        checkpoint = self.ledger.checkpoint()
        self.ledger.append("event", {"i": 5}, self.signer)
        self.assertTrue(verify(self.ledger.records(), self.trust, checkpoint).ok)

    def test_torn_line_is_not_repaired_silently(self):
        with self.ledger.path.open("a") as fh:
            fh.write('{"seq": 5, "bro')
        with self.assertRaises(LedgerCorrupt):
            self.ledger.append("event", {}, self.signer)

    def test_canonical_rejects_floats(self):
        with self.assertRaises(CanonicalError):
            canonical_bytes({"t": 21.5})
        self.assertEqual(canonical_bytes({"b": 1, "a": "x"}), b'{"a":"x","b":1}')

    def test_merkle_root_rfc6962_empty(self):
        self.assertEqual(
            merkle_root([]),
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        )


if __name__ == "__main__":
    unittest.main()
