import argparse
import logging
import sys
import time
from pathlib import Path

from qa_agent import chunker, pdf_loader, vector_store
from qa_agent.config import settings
from qa_agent.llm_client import MimikUnavailableError, chat

logger = logging.getLogger(__name__)

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


def _cmd_ingest(args: argparse.Namespace) -> None:
    """Handle the ingest subcommand — load, chunk, embed, and store a PDF."""
    pdf_path: Path = args.pdf_path
    start = time.monotonic()

    logger.info(f"ingestion_started path={pdf_path}")

    try:
        pages = pdf_loader.load_pdf(pdf_path)
    except FileNotFoundError:
        print(f"Error: PDF not found at {pdf_path}", file=sys.stderr)
        sys.exit(1)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        chunks = chunker.chunk_texts(pages, settings.chunk_size, settings.chunk_overlap)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    logger.info(
        f"chunks_generated count={len(chunks)} "
        f"chunk_size={settings.chunk_size} overlap={settings.chunk_overlap}"
    )

    vector_store.add_chunks(chunks)

    duration = round(time.monotonic() - start, 2)
    logger.info(f"ingestion_completed duration_s={duration}")
    print(f"Ingested {len(chunks)} chunks from {pdf_path} in {duration}s")


def main() -> None:
    """Entry point for the qa-agent CLI."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

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

    ingest_parser = subparsers.add_parser(
        "ingest", help="Ingest a PDF into the vector store."
    )
    ingest_parser.add_argument("pdf_path", type=Path)
    ingest_parser.set_defaults(func=_cmd_ingest)

    args = parser.parse_args()
    args.func(args)
