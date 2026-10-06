# Agent instructions

This repo is a small fictional customer-service demo for Harborline Finance. Keep it small enough to walk through in a couple of minutes.

## Stack

- Python 3, standard library only. No API keys, no network calls, and no extra packages.
- Do not add a hosted LLM. Answers are retrieved from `data/` and composed in code.
- Fake data only. Never add real customer data, credentials, tokens, or other secrets.

## Behavior that must stay true

- Money movement is impossible. `harborline/policy.py` refuses wire, transfer, and send-money requests with a deterministic check before an answer is composed.
- `harborline/store.py` is read-only. Do not add a path that writes balances or simulates a completed transfer.

## When you make a meaningful choice

- Append it to `docs/decisions.md` with the date and why you chose it.
- Run `python3 -m unittest discover -s tests -v` before you finish.
