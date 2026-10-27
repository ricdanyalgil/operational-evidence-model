import unittest
from datetime import datetime, timedelta, timezone

from oem.evidence import (
    Attestation,
    Record,
    Status,
    Trust,
    edge_verdict,
    gateway_verdict,
)

NOW = datetime(2026, 10, 27, 10, 0, tzinfo=timezone.utc)
CAL = NOW + timedelta(days=90)


def captured(rid, source, attested=True, signed=True, calibrated_until=CAL, **kw):
    return Record(
        record_id=rid,
        source_id=source,
        captured_at=NOW,
        payload_digest="sha256:" + rid,
        signature_valid=signed,
        attestation=Attestation(source, attested, calibrated_until),
        **kw,
    )


class EdgeTest(unittest.TestCase):
    def test_attested_record_is_evidence(self):
        v = edge_verdict(captured("r1", "cam-01"), received_at=NOW)
        self.assertEqual(v.status, Status.EVIDENCE)
        self.assertEqual(v.tau, Trust.DEVICE_ATTESTED)

    def test_signed_but_unattested_is_kept_and_flagged(self):
        v = edge_verdict(captured("r1", "cam-01", attested=False), received_at=NOW)
        self.assertEqual(v.status, Status.FLAGGED)
        self.assertEqual(v.tau, Trust.SIGNED_AT_CAPTURE)

    def test_expired_calibration_fails_phi4(self):
        v = edge_verdict(captured("r1", "cam-01", calibrated_until=NOW - timedelta(days=1)), received_at=NOW)
        self.assertFalse(next(c for c in v.checks if c.condition == "phi4").passed)

    def test_future_capture_fails_phi3(self):
        v = edge_verdict(captured("r1", "cam-01"), received_at=NOW - timedelta(minutes=5))
        self.assertEqual(v.status, Status.FLAGGED)


class GatewayTest(unittest.TestCase):
    def test_phi2_ai_output_cannot_exceed_its_inputs(self):
        weak = captured("in1", "cam-01", attested=False)              # signed only
        derived = captured("ai1", "fusion-gw", derived_from=("in1",), transformation="ai:detector-v3")
        graph = {r.record_id: r for r in (weak, derived)}
        v = gateway_verdict(derived, graph, received_at=NOW)
        self.assertEqual(v.tau, Trust.SIGNED_AT_CAPTURE)
        self.assertEqual(v.status, Status.FLAGGED)
        self.assertIn("ai:detector-v3", v.kappa["rules"][-1]["reason"])

    def test_corroboration_by_independent_source_raises_tau(self):
        a = captured("a", "cam-01", corroborated_by=("b",))
        b = captured("b", "lidar-02")
        v = gateway_verdict(a, {"a": a, "b": b}, received_at=NOW)
        self.assertEqual(v.tau, Trust.CORROBORATED)
        self.assertEqual(v.status, Status.EVIDENCE)

    def test_same_source_does_not_corroborate_itself(self):
        a = captured("a", "cam-01", corroborated_by=("b",))
        b = captured("b", "cam-01")
        v = gateway_verdict(a, {"a": a, "b": b}, received_at=NOW)
        self.assertEqual(v.tau, Trust.DEVICE_ATTESTED)

    def test_unknown_input_is_flagged(self):
        d = captured("d", "gw", derived_from=("missing",), transformation="agg:mean")
        v = gateway_verdict(d, {"d": d}, received_at=NOW)
        self.assertEqual(v.status, Status.FLAGGED)
        self.assertEqual(v.tau, Trust.UNVERIFIED)

    def test_kappa_lists_every_rule_applied(self):
        r = captured("r", "cam-01")
        k = gateway_verdict(r, {"r": r}, received_at=NOW).kappa
        self.assertEqual([x["condition"] for x in k["rules"]], ["phi1", "phi3", "phi4", "phi2"])
        self.assertEqual(k["stage"], "gateway")


if __name__ == "__main__":
    unittest.main()
