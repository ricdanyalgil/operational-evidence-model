# Contributing

This is doctoral research, open so that it can be checked and reused. Contributions that are especially useful:

- **Break the ledger.** Find a tamper the verifier misses and report it privately (see SECURITY.md).
- **Argue with Φ2.** A case where capping a derived record's trust at its weakest input is wrong, or a precedent we have not cited.
- **Write a verifier in another language** from `src/oem/ledger.py` and `ledger/README.md`.

Run `python -m unittest discover -s tests -v` before opening a pull request. Only the doctoral candidate appends to `ledger/research.jsonl`.

Contributors are acknowledged in the thesis unless they ask not to be.

## Licensing of contributions

The project is licensed for non-commercial use (PolyForm Noncommercial 1.0.0, CC BY-NC 4.0) and offered commercially under separate paid licences. By opening a pull request you agree that your contribution may be distributed under both: the public non-commercial licences and the commercial licences granted by the author. If you cannot agree to that, open an issue instead of a pull request.
