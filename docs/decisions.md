# Decisions

## 2026-10-06 — Python standard library, retrieval answers, hard policy gate

Harborline Finance is a fictional company. The demo has to run locally and in CI with no API keys, so the agent is plain Python 3 and uses only the standard library.

There is no LLM. A customer question is handled in three steps:

1. **Policy gate.** `harborline/policy.py` decides whether the question is a request to wire, transfer, or send money. The check is a set of patterns, not a model judgment.
2. **Read-only lookup.** `harborline/store.py` reads markdown in `data/docs/` and the three JSON records in `data/customers/`. It has no write API.
3. **Templated answer.** `harborline/agent.py` turns the retrieved account or policy text into a short reply. A refused request still cites the money-movement policy, and the reply says that no transfer was executed.

The interface is a CLI (`python3 -m harborline`) rather than an HTTP service, so the office-hours walkthrough is one command and the tests can spawn it without a port. A refusal exits 2. An ordinary answer exits 0. Both are successful runs of the agent; the exit code tells a demo script which path it took.

Customer names, emails, account ids, and balances in `data/customers/` are invented. Emails use `example.com`.
