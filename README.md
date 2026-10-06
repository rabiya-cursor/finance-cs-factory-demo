# Harborline Finance customer-service demo

A tiny, self-contained agent for a fictional finance company. It looks up company policies and three invented customer records, answers ordinary questions from that context, and refuses requests to wire, transfer, or send money.

Nothing here calls a model or the network. Customer names, account ids, balances, and emails are fake.

```
question → policy gate → read-only lookup → templated answer
```

If the question asks the agent to move money, the gate refuses before an answer is composed. The money-movement policy is still retrieved so the refusal can cite it. Account files are never written.

## Install

Python 3.10 or newer. There is nothing to install.

```bash
python3 --version
```

## Run the agent

From the repo root:

```bash
python3 -m harborline "what's my balance?" --customer HL-10021
python3 -m harborline "what's the fee policy?"
python3 -m harborline "transfer $10000 to Jordan Hale" --customer HL-10021
```

The first two commands answer from the customer record or `data/docs/fee-policy.md` and exit 0. The transfer command prints `REFUSED` and `No transfer was executed`, cites `data/docs/money-movement-policy.md`, and exits 2. Exit 2 means the policy gate refused the request. It does not mean the program crashed.

Add `--json` for a machine-readable result. `--customer` accepts an account id, an email, or an exact name (`HL-10021`, `maya.chen@example.com`, or `Maya Chen`). A name or account id inside the question works too.

## Run the tests

```bash
python3 -m unittest discover -s tests -v
```

## Layout

| Path | What it is |
| --- | --- |
| `harborline/policy.py` | Deterministic wire / transfer / send-money refusal |
| `harborline/store.py` | Read-only document and customer lookup |
| `harborline/agent.py` | Ties the gate, lookup, and answer together |
| `data/docs/` | Fee schedule, FAQ, and money-movement policy |
| `data/customers/` | Maya Chen, Jordan Hale, and Priya Nandakumar |
| `docs/decisions.md` | Why the stack looks like this |

Fictional accounts:

| Name | Account | Email | Balance |
| --- | --- | --- | --- |
| Maya Chen | HL-10021 | maya.chen@example.com | $4,250.18 |
| Jordan Hale | HL-10058 | jordan.hale@example.com | $890.40 |
| Priya Nandakumar | HL-10103 | priya.nandakumar@example.com | $12,640.55 |
