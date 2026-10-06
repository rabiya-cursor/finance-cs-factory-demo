"""Read-only company documents and fictional customer records."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import re

STOPWORDS = {
    "what",
    "whats",
    "what's",
    "is",
    "the",
    "my",
    "a",
    "an",
    "do",
    "does",
    "how",
    "i",
    "me",
    "of",
    "for",
    "to",
    "please",
    "you",
    "your",
    "our",
    "and",
    "or",
    "on",
    "in",
    "it",
    "this",
    "that",
    "can",
    "could",
    "would",
    "tell",
    "about",
    "with",
    "from",
    "are",
    "be",
}


def default_data_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "data"


def keywords(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9']+", text.lower())
    return [word for word in words if word not in STOPWORDS and len(word) > 2]


@dataclass(frozen=True)
class Customer:
    name: str
    account_id: str
    email: str
    balance_usd: float
    product: str
    source: str

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "account_id": self.account_id,
            "email": self.email,
            "balance_usd": self.balance_usd,
            "product": self.product,
            "source": self.source,
        }


@dataclass(frozen=True)
class Document:
    title: str
    body: str
    source: str

    def as_dict(self) -> dict:
        return {"title": self.title, "source": self.source, "body": self.body}


class Store:
    """Load fictional customers and company docs. Nothing here writes."""

    def __init__(self, data_dir: Path | None = None):
        self.data_dir = Path(data_dir) if data_dir else default_data_dir()

    def list_customers(self) -> list[Customer]:
        directory = self.data_dir / "customers"
        return [self._read_customer(path) for path in sorted(directory.glob("*.json"))]

    def list_documents(self) -> list[Document]:
        directory = self.data_dir / "docs"
        return [self._read_document(path) for path in sorted(directory.glob("*.md"))]

    def find_customer(self, query: str = "", customer_id: str | None = None) -> Customer | None:
        customers = self.list_customers()
        if customer_id:
            key = customer_id.strip().lower()
            for customer in customers:
                if key in {customer.account_id.lower(), customer.email.lower(), customer.name.lower()}:
                    return customer
            return None

        query_text = query.lower()
        for customer in customers:
            if customer.account_id.lower() in query_text:
                return customer
            if customer.email.lower() in query_text:
                return customer
            if customer.name.lower() in query_text:
                return customer
        return None

    def search_documents(self, query: str, limit: int = 2) -> list[Document]:
        tokens = keywords(query)
        if not tokens:
            return []
        scored: list[tuple[int, Document]] = []
        for document in self.list_documents():
            title = document.title.lower()
            body = document.body.lower()
            score = 0
            for token in tokens:
                if token in title:
                    score += 3
                if token in body:
                    score += 1
            if score:
                scored.append((score, document))
        scored.sort(key=lambda item: (-item[0], item[1].source))
        return [document for _, document in scored[:limit]]

    def _read_customer(self, path: Path) -> Customer:
        payload = json.loads(path.read_text(encoding="utf-8"))
        required = ["name", "account_id", "email", "balance_usd", "product"]
        missing = [key for key in required if key not in payload]
        if missing:
            raise ValueError(f"{path.name} is missing {', '.join(missing)}")
        return Customer(
            name=str(payload["name"]),
            account_id=str(payload["account_id"]),
            email=str(payload["email"]),
            balance_usd=float(payload["balance_usd"]),
            product=str(payload["product"]),
            source=self._relative(path),
        )

    def _read_document(self, path: Path) -> Document:
        text = path.read_text(encoding="utf-8").strip()
        lines = text.splitlines()
        title = "Untitled"
        body = text
        if lines and lines[0].startswith("# "):
            title = lines[0][2:].strip()
            body = "\n".join(lines[1:]).strip()
        return Document(title=title, body=body, source=self._relative(path))

    def _relative(self, path: Path) -> str:
        try:
            return path.relative_to(self.data_dir.parent).as_posix()
        except ValueError:
            return path.as_posix()
