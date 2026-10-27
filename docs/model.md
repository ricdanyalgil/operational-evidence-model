# The model, and what the code does with it

`src/oem/evidence.py` is an executable sketch, written so the ideas can be tested and argued about. It is not the formal model. Where they disagree, the work plan wins.

## Trust levels (τ)

| Level | Meaning |
|---|---|
| `unverified` | No valid capture signature |
| `signed_at_capture` | Signed at capture, but the device is not attested or not in calibration |
| `device_attested` | Signed by an attested device that was in calibration at capture time |
| `corroborated` | Device-attested and confirmed by an independent source that is itself device-attested |

Because Φ4 requires device attestation, every record with status `evidence` is at least `device_attested`. Records at the two lower levels are kept and flagged; they never disappear, they just do not count as evidence.

## Conditions (Φ)

| Condition | Where | In the sketch | In the formal model |
|---|---|---|---|
| Φ1 | edge | Source, capture time and payload digest present; derived records name their transformation | SHACL shape over PROV-O |
| Φ2 | gateway | τ of a derived record is capped by the least trusted input; only independent corroboration raises it | Extended logic programming with QoI/DoC |
| Φ3 | edge | Capture time not later than reception plus clock skew | SHACL shape |
| Φ4 | edge | Valid capture signature, device attested, calibration valid at capture time | SHACL shape plus device attestation |

Φ1 and Φ3 in the sketch are provisional placeholders. Their definitive form is set in Task 2.

## Justification (κ)

Every gateway verdict exports `kappa`: the record, the stage, the status, τ and the list of rules applied with their result and reason. κ is issued only at the gateway, after Φ2, because it needs the provenance graph. The edge returns a verdict on Φ1, Φ3 and Φ4, which is what hypothesis H3 times.

## What the sketch does not do yet

- No ontology; the provenance graph is a Python mapping.
- No QoI/DoC values; τ is ordinal only.
- No real device attestation; `Attestation` is supplied by the caller.
- No anchoring to a blockchain; the ledger produces Merkle checkpoints that an anchor can take.

## Numbers

Readings are never floats in hashed data (see `canonical.py`). Use decimal strings (`"21.50"`) with an explicit unit, or scaled integers.

## The logo

The mark is the evidence gate: a ring with one opening, a record (the small square) at the opening, and the core inside. Data only becomes evidence by passing through the gate, and every record that passes carries its justification. Files are in `docs/assets/`: `oem-mark.svg` (light backgrounds), `oem-mark-dark.svg` (dark backgrounds), `oem-icon.svg` and `oem-icon-512.png` (app icon), `oem-social.png` (1280×640 preview). Colours: navy `#0B1426`, ink `#E8EEF7`, cyan `#3DD6F5` (dark) / `#0A8FB3` (light).
