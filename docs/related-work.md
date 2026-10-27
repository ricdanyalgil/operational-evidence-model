# Related work

A working list for the systematic review of Task 1. It records where OEM borrows and where it differs; it is not the review.

## Tamper-evident logs

- Haber & Stornetta (1991), time-stamping; Schneier & Kelsey (1999), secure audit logs; Crosby & Wallach (2009), history trees.
- Certificate Transparency, RFC 6962 and RFC 9162: Merkle-tree logs with external auditors. OEM uses the RFC 6962 tree hash for its checkpoints.

## Agent flight recorders

- **Tracekit** (Ghosh, 2026; github.com/Cygnux-Labs/Tracekit, MIT): signs every tool call and policy decision of an AI agent into a hash chain, with witnesses and an offline verifier. Ideas adopted in OEM: self-report as testimony and checks as evidence; no silent repair of a log; published limits. Difference: Tracekit governs what an agent does; OEM decides what operational data is worth before it is recorded.
- Similar tools found in October 2026: TraceVault, Retrace, Mnestiq, BLACKBOX, Agentmetry. None assigns an evidential status to sensor data.

## Pre-anchoring validation (nearest competitors)

- Zhang, Li, Qin, Wang & Chen (2026), *Applied Sciences* 16(18), 9011: continuous trust scoring for three-level pre-chain admission of IoT streams. Closest to OEM. Differences: a learned score instead of rules, no per-record justification, provenance and single-source settings out of scope.
- Bigiotti, Mostarda & Navarra (2026), IoTrust, AINA 2026.
- Yuan (2026), preprint: blockchain anchoring proves post-capture continuity only.

## Provenance and validation

- W3C PROV-O; SHACL; Oudshoorn et al. (2026) on SHACL validation with ontologies (Horn DLs); Sharma & Kunkel (2026), OWL–SHACL–PROV-O compliance stack (preprint).
- University of Minho line on reasoning under incomplete information: Lima et al. (2011), Neves et al. (2015), Machado, Sousa et al. (2024).

## To search

Precedents for Φ2: trust propagation through provenance (fuzzy and Bayesian work from the 2010s). If they exist, they are cited before a reviewer finds them.
