<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/assets/oem-mark-dark.svg">
    <img src="docs/assets/oem-mark.svg" alt="OEM logo: a record passing through the evidence gate" width="120">
  </picture>
</p>

# OEM — Operational Evidence Model

**Anchoring a record on a blockchain proves it was not changed afterwards. It does not prove it was true when it was captured.**
OEM is the doctoral research that works on the step before the anchor: deciding, with an explicit and auditable justification, whether a piece of operational data counts as evidence at all.

[![CI](https://github.com/ricdanyalgil/operational-evidence-model/actions/workflows/ci.yml/badge.svg)](https://github.com/ricdanyalgil/operational-evidence-model/actions/workflows/ci.yml)
[![Licence: PolyForm Noncommercial](https://img.shields.io/badge/code-PolyForm%20Noncommercial-blue?style=flat-square)](LICENSE)
[![Docs: CC BY-NC 4.0](https://img.shields.io/badge/docs-CC%20BY--NC%204.0-lightgrey?style=flat-square)](LICENSE-docs)
[![Commercial use: licence required](https://img.shields.io/badge/commercial%20use-licence%20required-red?style=flat-square)](COMMERCIAL.md)
[![Status](https://img.shields.io/badge/status-year%201%20of%204-orange?style=flat-square)](#milestones)

Doctoral programme in Informatics (PDInf) · University of Minho · ALGORITMI Research Centre / LASI

---

## Contents

[The problem](#the-problem) · [The model](#the-model) · [Research question](#research-question-and-hypotheses) · [Milestones](#milestones) · [Traceability of this research](#traceability-of-this-research) · [Run it](#run-it) · [Repository map](#repository-map) · [Team](#research-team) · [Related work](#related-work-and-acknowledgements) · [Cite](#cite) · [Resumo em português](#resumo-em-português)

## The problem

Cyber-physical systems (security towers, industrial lines, IoT fleets) increasingly write their sensor data and AI outputs to immutable ledgers, so that the records can later serve as evidence for an operator, an auditor or a court. The ledger guarantees *post-capture continuity*: what was written is still what was written. It says nothing about whether the sensor was calibrated, whether the device was the one it claimed to be, or whether an AI model upstream turned a weak signal into a confident alert.

Regulation is moving in the same direction. The EU AI Act asks high-risk systems to keep logs (Art. 12) and asks deployers to ensure the relevance of input data (Art. 26(4)); the Digital Omnibus on AI, Regulation (EU) 2026/1744, postpones these obligations to 2 December 2027 (Annex III) and 2 August 2028 (Annex I) but does not remove them. Logging is required. What makes a logged record *trustworthy evidence* is left open.

## The model

```
OEM = ⟨ S, P, R, τ, Φ, κ ⟩
```

| Symbol | Meaning |
|---|---|
| **S** | Sources: sensors, devices, operators |
| **P** | Provenance graph linking each record to its sources and to the records it was derived from (PROV-O) |
| **R** | Records, captured or derived |
| **τ** | Ordinal trust: `unverified < signed at capture < calibrated-device attested < corroborated by independent sources` |
| **Φ** | Conditions a record must meet to count as evidence (Φ1–Φ4) |
| **κ** | Justification issued for every record: which rules fired, and why the record has the status it has |

Two ideas carry the contribution:

- **Φ2, no trust amplification.** A record derived from other records (by aggregation, fusion or an AI model) can never be trusted more than the least trusted of its inputs. The only way up is corroboration by an *independent* source.
- **κ, a justification per record.** Every record gets an explicit status and the trace of the rules that produced it, so the status can be contested and re-derived by a third party.

The architecture has three layers: **edge sensing** (Φ1, Φ3 and Φ4 checked on the device or next to it), **intelligent processing** (the evidence gateway, where Φ2 is checked against the provenance graph and κ is issued) and **immutable registration** (Merkle-tree anchoring of what passed, and of what did not, with its status).

The formalism under development combines OWL 2 RL and PROV-O for the provenance graph, SHACL shapes for Φ1, Φ3 and Φ4, and extended logic programming with Quality-of-Information / Degree-of-Confidence annotations, a line of work of the University of Minho, for τ and Φ2. The code in this repository is a provisional executable sketch of the model; see [docs/model.md](docs/model.md).

## Research question and hypotheses

> How can operational data from cyber-physical systems be validated and justified *before* it is anchored, so that the resulting records are admissible as evidence and contestable by third parties, without relying on learned trust scores alone?

The work follows Design Science Research (Peffers et al.) with the FEDS evaluation framework, in four DSR cycles. The hypotheses (H1–H5) cover traceability completeness, detection of invalid records against baselines, latency of the edge verdict (target: p95 below 500 ms from capture to edge verdict, with ledger confirmation reported separately), contestability through κ, and generalisation beyond the first domain. The full statements, metrics and baselines are in the doctoral work plan.

## Milestones

The plan runs from March 2026 to September 2029, with tasks that overlap so that each DSR cycle starts while the previous one closes.

| # | Task | Period | Main outputs | Status |
|---|---|---|---|---|
| **T1** | Delimitation, systematic mapping and work plan | Mar 2026 – Feb 2027 | Systematic review (focus: precedents for Φ2 and trust propagation in provenance), research gap, approved work plan | 🟡 in progress |
| **T2** | Formal specification of the OEM and reference architecture | Oct 2026 – Sep 2027 | OEM in OWL 2 RL + PROV-O, Φ1/Φ3/Φ4 as SHACL shapes, τ and Φ2 in QoI/DoC logic programming, benchmark against SHACL-SPARQL | 🟡 started (this repository) |
| **T3** | In-vivo validation in a living lab (≥ 12 months) | Oct 2027 – Sep 2028 | Deployment on a cyber-physical security tower with the industrial partner; H1–H4 tested on operational data | ⚪ planned |
| **T4** | Generalisation, thesis and defence | Oct 2028 – Sep 2029 | Second domain, thesis, public defence | ⚪ planned |

Checkpoints inside the tasks:

- [x] Work plan v3 reviewed by the supervisors; QoI/DoC adopted as the rule formalism (Oct 2026)
- [x] Public repository and signed research ledger opened (Oct 2026)
- [ ] Work plan v4 with the verification corrections, and its defence
- [ ] Systematic review protocol registered
- [ ] OEM ontology v1 (OWL 2 RL + PROV-O) published in `ontology/`
- [ ] SHACL shapes for Φ1, Φ3, Φ4 and the QoI/DoC rules for τ and Φ2
- [ ] Evidence gateway prototype meeting the H3 latency budget
- [ ] Living-lab deployment begins
- [ ] Dissemination: four journal articles and two conference papers planned

The detailed and dated list lives in [docs/milestones.md](docs/milestones.md). Every change of status is also written to the research ledger below.

## Traceability of this research

This repository applies the idea it studies to itself. Milestones, method decisions, dataset versions and publications are appended to [`ledger/research.jsonl`](ledger/), a hash-chained ledger in which each record is signed with Ed25519 over canonical JSON. Its checkpoints use RFC 6962 Merkle roots and are anchored outside the repository, so a rewritten history or a cut-off tail can be detected, not just a single edited line.

```sh
oem verify ledger/research.jsonl --trust ledger/trust.json --checkpoint ledger/checkpoints/latest.json
```

Continuous integration runs this check on every push. What the ledger proves and what it does not is spelled out in [ledger/README.md](ledger/README.md).

## Run it

Python 3.10 or newer.

```sh
git clone https://github.com/ricdanyalgil/operational-evidence-model.git && cd operational-evidence-model
pip install -e .
oem demo                                  # write three records, tamper with them, watch verification fail
python -m unittest discover -s tests -v   # 19 tests: ledger integrity and the OEM conditions
```

`oem demo` shows the two halves of the integrity story: an edited record fails at that record, and a deleted last record passes the chain alone but fails against a checkpoint.

```text
== someone edits record 1 after the fact (zone B -> zone C)
[FAIL] 3 record(s) checked
        seq 1: hash does not match the record
Integrity: FAILED.

== instead, the last record is deleted (the chain alone cannot see it)
Integrity: VERIFIED. (chain alone)
[FAIL] 2 record(s) checked
        ledger has 2 record(s) but the checkpoint saw 3 (tail cut off)
Integrity: FAILED. (with checkpoint)
```

## Repository map

| Path | What it holds |
|---|---|
| `src/oem/evidence.py` | τ, Φ1–Φ4 and κ: edge and gateway verdicts (provisional sketch) |
| `src/oem/ledger.py` | Signed, hash-chained ledger, RFC 6962 Merkle checkpoints, offline verifier |
| `src/oem/canonical.py` | Canonical JSON for hashing and signing |
| `src/oem/cli.py` | `oem keygen · append · verify · checkpoint · demo` |
| `ledger/` | The research ledger of this doctorate, its trusted keys and checkpoints |
| `docs/` | Model, milestones, related work |
| `ontology/` | OWL / PROV-O / SHACL artefacts (from T2) |

## Research team

| Role | Name | Affiliation |
|---|---|---|
| Doctoral candidate | **Ricardo Danyalgil Junior** | University of Minho · ALGORITMI / LASI |
| Supervisor | **Prof. José Manuel Machado** | University of Minho · ALGORITMI |
| Co-supervisor | **Prof. José Luís Reis** | University of Minho · ALGORITMI |
| Industrial partner (living lab) | **Danyalgil & Danyalgil, Lda.** | Fundão, Portugal |

The in-vivo validation builds on a cyber-physical security tower covered by patent PT 119572 A.

## Related work and acknowledgements

OEM sits between three bodies of work: tamper-evident logging (Haber & Stornetta; Schneier & Kelsey; Crosby & Wallach; Certificate Transparency, RFC 6962/9162), provenance (W3C PROV-O) and the blockchain oracle problem, in which the chain cannot vouch for what enters it.

This repository was written from scratch. Its integrity layer was informed by **[Tracekit](https://github.com/Cygnux-Labs/Tracekit)** (Bravish Ghosh, Cygnux Labs, MIT; [arXiv:2609.35659](https://arxiv.org/abs/2609.35659)), a tamper-evident flight recorder for AI agents. Three of its design choices are adopted here: treating a component's account of itself as *testimony* and what can be checked as *evidence*; never repairing a log silently; and publishing the limits of what verification proves. No code was copied. The difference in scope: Tracekit records and gates what an agent *does*; OEM decides what operational data *is worth* before it is recorded. Further comparisons are in [docs/related-work.md](docs/related-work.md).

## Cite

See [CITATION.cff](CITATION.cff), or:

```bibtex
@software{danyalgil_oem_2026,
  author  = {Danyalgil Junior, Ricardo and Machado, José Manuel and Reis, José Luís},
  title   = {{OEM}: Operational Evidence Model},
  year    = {2026},
  version = {0.1.0},
  note    = {Doctoral research, University of Minho}
}
```

## Licence

The source is open to read, study, reproduce and build on for **non-commercial** purposes: research, teaching, personal use, and use by non-profit, educational and public-research organisations.

- Code: [PolyForm Noncommercial License 1.0.0](LICENSE)
- Documentation, ontology and figures: [CC BY-NC 4.0](LICENSE-docs)
- **Commercial use requires a separate paid licence (royalties).** See [COMMERCIAL.md](COMMERCIAL.md).

Nothing in this repository grants rights over patent PT 119572 A beyond what these licences state.

---

## Resumo em português

O **OEM (Operational Evidence Model)** é o trabalho de doutoramento de Ricardo Danyalgil Junior no Programa Doutoral em Informática da Universidade do Minho (Centro ALGORITMI / LASI), orientado pelos Professores José Manuel Machado e José Luís Reis. A ancoragem em blockchain prova que um registo não foi alterado depois de escrito, mas não prova que era verdadeiro quando foi captado. O OEM trata do passo anterior: atribui a cada registo operacional um estatuto (evidência ou não), um nível ordinal de confiança τ e uma justificação κ auditável, e impede que transformações, incluindo modelos de IA, aumentem a confiança dos dados que recebem (regra Φ2). A metodologia é Design Science Research, em quatro ciclos (T1 a T4, de março de 2026 a setembro de 2029), com validação in vivo num living lab com a Danyalgil & Danyalgil, Lda. O código é aberto para consulta e uso não comercial (investigação, ensino, uso pessoal e instituições sem fins lucrativos); o uso comercial exige uma licença paga, com royalties (ver COMMERCIAL.md). O repositório regista os marcos da investigação num ledger assinado e verificável, aplicando à própria tese a rastreabilidade que ela estuda.
