#!/usr/bin/env python3
"""Count tokens in text using tiktoken, with word-count fallback.

Usage:
    poetry run python scripts/token_count.py "some text"
    echo "some text" | poetry run python scripts/token_count.py

Intended for Step 9 prompt-size diagnostics.
"""
import argparse
import sys

try:
    import tiktoken
except ImportError:
    tiktoken = None


def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    """Return tiktoken count if available, else word count."""
    if tiktoken is None:
        return len(text.split())
    try:
        enc = tiktoken.get_encoding(encoding_name)
        return len(enc.encode(text))
    except Exception:
        return len(text.split())


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Count tokens in text (uses tiktoken when available, word count fallback)."
    )
    parser.add_argument(
        "text",
        nargs="*",
        help="Text to count. Reads stdin if omitted.",
    )
    parser.add_argument(
        "--encoding",
        default="cl100k_base",
        help="tiktoken encoding name (default: cl100k_base).",
    )
    args = parser.parse_args()

    text = " ".join(args.text) if args.text else sys.stdin.read()
    if not text.strip():
        print("No input text provided.", file=sys.stderr)
        sys.exit(2)

    count = count_tokens(text, args.encoding)
    print(count)


if __name__ == "__main__":
    main()
