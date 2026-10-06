"""Deterministic refusal for requests to move money.

This is a policy gate, not a model judgment. If a query asks Harborline to
wire, transfer, or send money, the agent refuses before it composes an answer.
"""

from __future__ import annotations

import re

# A question about fees, policies, or how something works. These may mention
# wires without asking the agent to move money.
_INFORMATIONAL = re.compile(
    r"^\s*(what|what's|whats|how|when|where|why|which|who|is|are|do|does|did|"
    r"can i|could i|tell me|explain)\b",
    re.IGNORECASE,
)

_FEE_TOPIC = re.compile(
    r"\b(fee|fees|policy|policies|faq|cost|costs|charge|charges)\b",
    re.IGNORECASE,
)

_AGENT_REQUEST = re.compile(
    r"\b(?:please|can you|could you|would you|"
    r"i want(?: you)? to|i need(?: you)? to|"
    r"i'd like(?: you)? to|i would like(?: you)? to|"
    r"go ahead and|kindly)\b",
    re.IGNORECASE,
)

_MOVEMENT_WORD = r"(?:wir(?:e|ing)|transfer(?:ring)?|send(?:ing)?|mov(?:e|ing))"

_LEADING_IMPERATIVE = re.compile(
    rf"^\s*(?:please\s+)?{_MOVEMENT_WORD}\b",
    re.IGNORECASE,
)

_MOVEMENT = re.compile(rf"\b{_MOVEMENT_WORD}\b", re.IGNORECASE)

_AMOUNT = re.compile(
    r"\$\s?\d[\d,]*(?:\.\d+)?|\b\d[\d,]*(?:\.\d+)?\s*(?:dollars|usd|bucks)\b",
    re.IGNORECASE,
)

_INITIATE = re.compile(
    r"\b(?:initiate|execute|process|complete|make)\b"
    r"(?:\s+\w+){0,4}\s+"
    r"(?:a\s+|an\s+|the\s+)?(?:wire|transfer|payment|ach)\b",
    re.IGNORECASE,
)

_SEND_OBJECT = re.compile(
    rf"\b{_MOVEMENT_WORD}\s+(?:me\s+)?(?:some\s+|the\s+|my\s+)?(?:money|funds|cash)\b",
    re.IGNORECASE,
)

_ASK_VERB = re.compile(
    r"\b(?:please|can you|could you|would you|"
    r"i want(?: you)? to|i need(?: you)? to|"
    r"i'd like(?: you)? to|i would like(?: you)? to|"
    r"go ahead and|kindly)\s+(?:please\s+)?(\w+)",
    re.IGNORECASE,
)

_MOVEMENT_VERBS = {
    "wire",
    "wiring",
    "transfer",
    "transferring",
    "send",
    "sending",
    "move",
    "moving",
}


def _movement_is_the_ask(text: str) -> bool:
    match = _ASK_VERB.search(text)
    if match is None:
        return _LEADING_IMPERATIVE.search(text) is not None
    return match.group(1).lower() in _MOVEMENT_VERBS


def classify_money_movement(text: str) -> str | None:
    """Return a refusal reason code, or None when the query is allowed.

    Reason codes:
    - amount_with_movement: a transfer, wire, or send verb paired with an amount
    - imperative_movement: the query tells the agent to move money or funds
    - initiate_payment: the query asks to initiate or execute a payment
    """

    query = " ".join(text.strip().split())
    if not query:
        return None

    informational = _INFORMATIONAL.search(query) is not None
    fee_question = _FEE_TOPIC.search(query) is not None
    agent_request = _AGENT_REQUEST.search(query) is not None
    leading = _LEADING_IMPERATIVE.search(query) is not None
    movement = _MOVEMENT.search(query) is not None
    amount = _AMOUNT.search(query) is not None
    initiate = _INITIATE.search(query) is not None
    topical = informational and fee_question and not agent_request and not leading

    if movement and amount and not topical:
        how_to = informational and query.lower().startswith("how") and not agent_request and not leading
        if not how_to:
            return "amount_with_movement"

    if _SEND_OBJECT.search(query) and not (informational and not agent_request):
        return "imperative_movement"

    if leading and (amount or re.search(r"\b(?:money|funds|cash|to)\b", query, re.IGNORECASE)):
        if not topical:
            return "imperative_movement"

    if agent_request and _movement_is_the_ask(query):
        return "imperative_movement"

    if initiate and not (informational and not agent_request):
        return "initiate_payment"

    return None


def is_money_movement_request(text: str) -> bool:
    return classify_money_movement(text) is not None
