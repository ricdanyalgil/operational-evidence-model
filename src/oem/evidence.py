"""Reference implementation of the Operational Evidence Model (OEM).

OEM = <S, P, R, tau, Phi, kappa>

  S      sources (sensors, devices, operators)
  P      the provenance graph linking records to sources and to each other
  R      records captured or derived in the system
  tau    an ordinal trust function over records
  Phi    the conditions a record must meet to count as evidence
  kappa  the justification issued for each record's status

This module is a *provisional, executable sketch* used to test the ideas in the
thesis. The normative definitions are those of the doctoral work plan (sec. 5.2),
where tau and Phi2 are written as extended logic programming rules with
Quality-of-Information / Degree-of-Confidence annotations and Phi1, Phi3 and
Phi4 as SHACL shapes over a PROV-O graph. Where this file and the work plan
disagree, the work plan wins and this file is the bug.

Placement follows the architecture: Phi1, Phi3 and Phi4 can be checked at the
edge on one record; Phi2 needs the provenance graph and is checked at the
evidence gateway, which is the only place kappa is issued.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import IntEnum
from typing import Mapping


class Trust(IntEnum):
    """Ordinal trust levels (tau). Order matters; arithmetic does not."""

    UNVERIFIED = 0
    SIGNED_AT_CAPTURE = 1
    DEVICE_ATTESTED = 2      # signed by a device with valid attestation and calibration
    CORROBORATED = 3         # attested and confirmed by an independent source


class Status:
    EVIDENCE = "evidence"    # meets every condition in Phi
    FLAGGED = "flagged"      # kept and traceable, but does not count as evidence


@dataclass(frozen=True)
class Attestation:
    device_id: str
    attested: bool
    calibrated_until: datetime | None


@dataclass(frozen=True)
class Record:
    record_id: str
    source_id: str
    captured_at: datetime
    payload_digest: str
    signature_valid: bool = False
    attestation: Attestation | None = None
    derived_from: tuple[str, ...] = ()
    transformation: str | None = None          # e.g. "ai:detector-v3", "agg:mean"
    corroborated_by: tuple[str, ...] = ()


@dataclass(frozen=True)
class Check:
    condition: str
    passed: bool
    reason: str


@dataclass
class Verdict:
    record_id: str
    status: str
    tau: Trust
    checks: list[Check] = field(default_factory=list)
    stage: str = "edge"

    @property
    def kappa(self) -> dict:
        """Justification: which conditions were applied, how, and why."""
        return {
            "record": self.record_id,
            "stage": self.stage,
            "status": self.status,
            "tau": self.tau.name.lower(),
            "rules": [
                {"condition": c.condition, "passed": c.passed, "reason": c.reason}
                for c in self.checks
            ],
        }


# --- Conditions checked on a single record (edge) ----------------------------

def phi1_provenance_complete(r: Record) -> Check:
    """Phi1 (provisional): the record names its source, capture time and payload digest."""
    missing = [
        name
        for name, value in (
            ("source_id", r.source_id),
            ("captured_at", r.captured_at),
            ("payload_digest", r.payload_digest),
        )
        if not value
    ]
    if r.derived_from and not r.transformation:
        missing.append("transformation")
    if missing:
        return Check("phi1", False, f"missing provenance: {', '.join(missing)}")
    return Check("phi1", True, "source, capture time and payload digest present")


def phi3_temporally_consistent(
    r: Record, received_at: datetime, max_skew: timedelta = timedelta(seconds=5)
) -> Check:
    """Phi3 (provisional): capture time is not in the future beyond clock skew."""
    if r.captured_at > received_at + max_skew:
        return Check("phi3", False, "captured_at is later than reception plus allowed skew")
    return Check("phi3", True, "capture time consistent with reception")


def phi4_device_attested(r: Record) -> Check:
    """Phi4: signed at capture by a device that is attested and in calibration."""
    if not r.signature_valid:
        return Check("phi4", False, "no valid capture signature")
    a = r.attestation
    if a is None or not a.attested:
        return Check("phi4", False, "device attestation absent or failed")
    if a.calibrated_until is None or a.calibrated_until < r.captured_at:
        return Check("phi4", False, "device calibration expired at capture time")
    return Check("phi4", True, f"device {a.device_id} attested and in calibration")


def base_trust(r: Record, phi4: Check) -> Trust:
    if not r.signature_valid:
        return Trust.UNVERIFIED
    return Trust.DEVICE_ATTESTED if phi4.passed else Trust.SIGNED_AT_CAPTURE


def edge_verdict(r: Record, received_at: datetime | None = None) -> Verdict:
    """What the edge can decide on its own: Phi1, Phi3 and Phi4. No kappa is final here."""
    received_at = received_at or datetime.now(timezone.utc)
    checks = [
        phi1_provenance_complete(r),
        phi3_temporally_consistent(r, received_at),
        phi4_device_attested(r),
    ]
    status = Status.EVIDENCE if all(c.passed for c in checks) else Status.FLAGGED
    return Verdict(r.record_id, status, base_trust(r, checks[2]), checks, stage="edge")


# --- Conditions that need the provenance graph (gateway) ---------------------

def gateway_verdict(
    r: Record,
    graph: Mapping[str, Record],
    received_at: datetime | None = None,
    _cache: dict[str, Verdict] | None = None,
) -> Verdict:
    """Full Phi, including Phi2 (no trust amplification), and the justification kappa.

    Phi2: a record derived from other records can never be trusted more than the
    least trusted of its inputs, whatever transformation produced it (an AI model
    included). The only way up is corroboration by an *independent* source that
    is itself at least device-attested.
    """
    cache = {} if _cache is None else _cache
    if r.record_id in cache:
        return cache[r.record_id]

    edge = edge_verdict(r, received_at)
    checks = list(edge.checks)
    tau = edge.tau

    if r.derived_from:
        unknown = [i for i in r.derived_from if i not in graph]
        if unknown:
            checks.append(Check("phi2", False, f"inputs not in provenance graph: {', '.join(unknown)}"))
            tau = Trust.UNVERIFIED
        else:
            inputs = [gateway_verdict(graph[i], graph, received_at, cache) for i in r.derived_from]
            ceiling = min(v.tau for v in inputs)
            if tau > ceiling:
                tau = ceiling
            checks.append(
                Check(
                    "phi2",
                    all(v.status == Status.EVIDENCE for v in inputs),
                    f"tau capped at {ceiling.name.lower()} by inputs "
                    f"{', '.join(r.derived_from)} through {r.transformation}",
                )
            )
    else:
        checks.append(Check("phi2", True, "captured record; no inputs to inherit from"))

    independent = [
        graph[i]
        for i in r.corroborated_by
        if i in graph and graph[i].source_id != r.source_id
    ]
    corroborating = [
        c for c in independent
        if gateway_verdict(c, graph, received_at, cache).tau >= Trust.DEVICE_ATTESTED
    ]
    if corroborating and tau >= Trust.DEVICE_ATTESTED:
        tau = Trust.CORROBORATED
        checks.append(
            Check("corroboration", True,
                  f"confirmed by independent source(s) {', '.join(c.record_id for c in corroborating)}")
        )

    status = Status.EVIDENCE if all(c.passed for c in checks) else Status.FLAGGED
    verdict = Verdict(r.record_id, status, tau, checks, stage="gateway")
    cache[r.record_id] = verdict
    return verdict
