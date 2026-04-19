import argparse
import sys

from qa_agent.llm_client import MimikUnavailableError, chat

_PING_SYSTEM = "Reply with exactly the word 'pong' and nothing else."
_PING_USER = "ping"


def _cmd_ping(_args: argparse.Namespace) -> None:
    """Handle the ping subcommand."""
    try:
        reply = chat(_PING_SYSTEM, _PING_USER)
        print(f"mimik reachable. model reply: {reply}")
    except MimikUnavailableError as exc:
        print(f"Error: mimik is not reachable. {exc}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Entry point for the qa-agent CLI."""
    parser = argparse.ArgumentParser(
        prog="qa-agent",
        description="QA Expert Agent — ISTQB RAG mentor.",
    )
    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = True

    ping_parser = subparsers.add_parser(
        "ping", help="Check connectivity to mimik AI Foundation."
    )
    ping_parser.set_defaults(func=_cmd_ping)

    args = parser.parse_args()
    args.func(args)
