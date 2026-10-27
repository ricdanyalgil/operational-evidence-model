# Research ledger

`research.jsonl` is the signed history of this doctorate: milestones, method decisions, dataset versions, submissions and publications. One JSON record per line.

```json
{"v":1,"seq":3,"ts":"2026-10-27T10:30:00Z","kind":"milestone","body":{"title":"..."},
 "prev":"<hash of seq 2>","key_id":"...","hash":"...","sig":"..."}
```

## Verify

```sh
pip install -e .
oem verify ledger/research.jsonl --trust ledger/trust.json --checkpoint ledger/checkpoints/latest.json
```

## Append (the candidate's machine only)

```sh
oem append ledger/research.jsonl --kind milestone --title "Systematic review protocol registered" \
  --body '{"task":"T1","ref":"docs/milestones.md"}'
oem checkpoint ledger/research.jsonl > ledger/checkpoints/latest.json
```

Then anchor the checkpoint outside this repository (a qualified timestamp or a public chain) and record the anchor reference as the next ledger entry, of kind `anchor`.

## What verification proves, and what it does not

- **Proves:** every record is exactly as it was signed, in order, with nothing inserted, removed or swapped, by a key listed in `trust.json`.
- **Proves, with a checkpoint:** the history up to that checkpoint was not rewritten and its tail was not cut off.
- **Does not prove** that what a record says is true. A milestone marked done is the candidate's statement, signed; supervisors' approvals are recorded as references to their own documents.
- **Does not protect** records written after the latest anchored checkpoint from someone holding the signing key. Anchor at least after every milestone.

## Keys

`trust.json` lists the public keys accepted. Private keys never enter this repository. A key change is itself a ledger record, signed by the outgoing key.
