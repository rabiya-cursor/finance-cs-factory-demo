"""Answer customer questions from local documents and fictional accounts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from harborline.policy import classify_money_movement
from harborline.store import Customer, Document, Store

REFUSAL_LEAD = (
    "REFUSED: Harborline chat cannot wire, transfer, or send money. "
    "No transfer was executed."
)


@dataclass(frozen=True)
class AgentResult:
    refused: bool
    answer: str
    refusal_reason: str | None
    customer: dict | None
    documents: list[dict]

    def as_dict(self) -> dict:
        return {
            "refused": self.refused,
            "answer": self.answer,
            "refusal_reason": self.refusal_reason,
            "customer": self.customer,
            "documents": self.documents,
        }


def format_usd(amount: float) -> str:
    return f"${amount:,.2f}"


def answer_query(
    query: str,
    customer_id: str | None = None,
    data_dir: Path | None = None,
) -> AgentResult:
    """Look up context and answer, or refuse a money-movement request.

    The policy check runs first. A refusal still loads the money-movement
    policy (and the customer, when one was named) so the reply can cite them.
    Customer files are never updated.
    """

    store = Store(data_dir)
    reason = classify_money_movement(query)
    customer = store.find_customer(query, customer_id=customer_id)

    if reason:
        documents = _money_movement_docs(store)
        return AgentResult(
            refused=True,
            answer=_refusal_answer(reason, documents),
            refusal_reason=reason,
            customer=_public_customer(customer),
            documents=[document.as_dict() for document in documents],
        )

    documents = store.search_documents(query, limit=2)
    return AgentResult(
        refused=False,
        answer=_safe_answer(query, customer, documents),
        refusal_reason=None,
        customer=_public_customer(customer),
        documents=[document.as_dict() for document in documents],
    )


def _money_movement_docs(store: Store) -> list[Document]:
    matches = [document for document in store.list_documents() if "money-movement" in document.source]
    if matches:
        return matches[:1]
    return store.search_documents("money movement wire transfer policy", limit=1)


def _refusal_answer(reason: str, documents: list[Document]) -> str:
    lines = [
        REFUSAL_LEAD,
        f"Reason: {reason}.",
        "I can look up policies and account facts, and I will not move funds.",
    ]
    if documents:
        document = documents[0]
        lines.append(f"Policy ({document.source}): {document.body}")
    return "\n\n".join(lines)


def _safe_answer(query: str, customer: Customer | None, documents: list[Document]) -> str:
    parts: list[str] = []
    asks_balance = re.search(r"\bbalance\b", query, re.IGNORECASE) is not None
    asks_profile = re.search(r"\b(who is|look up|email|account)\b", query, re.IGNORECASE) is not None

    if asks_balance and customer is None:
        parts.append("I couldn't find that customer. Pass an account id such as HL-10021.")
    elif customer is not None and (asks_balance or asks_profile):
        parts.append(
            f"{customer.name} ({customer.account_id}, {customer.email}) has a "
            f"{customer.product} balance of {format_usd(customer.balance_usd)}."
        )

    for document in documents:
        parts.append(f"{document.title} ({document.source}): {document.body}")

    if parts:
        return "\n\n".join(parts)
    return (
        "I don't have a matching document or customer for that. "
        "Ask about a balance, an account id, or the fee policy."
    )


def _public_customer(customer: Customer | None) -> dict | None:
    if customer is None:
        return None
    return customer.as_dict()
