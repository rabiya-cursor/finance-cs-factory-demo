"""Command-line entry point for the Harborline demo agent."""

from __future__ import annotations

from pathlib import Path
import argparse
import json

from harborline.agent import answer_query


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="harborline",
        description="Answer a Harborline Finance question from fictional local records.",
    )
    parser.add_argument("query", help="Customer question, in quotes")
    parser.add_argument(
        "--customer",
        help="Account id, email, or exact customer name. Example: HL-10021",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Override the data directory (defaults to ./data)",
    )
    parser.add_argument("--json", action="store_true", help="Print the result as JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = answer_query(args.query, customer_id=args.customer, data_dir=args.data_dir)
    if args.json:
        print(json.dumps(result.as_dict(), indent=2))
    else:
        print(result.answer)
        print()
        print(f"Refused: {'yes' if result.refused else 'no'}")
        if result.customer:
            customer = result.customer
            print(f"Customer: {customer['name']} ({customer['account_id']})")
        if result.documents:
            print("Documents:")
            for document in result.documents:
                print(f"- {document['source']}")
    return 2 if result.refused else 0
