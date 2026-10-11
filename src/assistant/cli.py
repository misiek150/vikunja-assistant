import argparse
import logging
import sys
from pathlib import Path

from assistant.config import Settings
from assistant.container import Container
from assistant.errors import DomainError
from assistant.logging_setup import configure_logging
from assistant.models import Screenshot

_log = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="assistant")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("read", help="List screenshots in the input folder")
    for name, help_text in (
        ("analyze", "Send screenshots to Gemini (or mock) and print extracted tasks"),
        ("map", "Analyze and print the resulting Vikunja requests"),
    ):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("--file", type=Path, help="Process only this image")
    run = sub.add_parser("run", help="Full pipeline")
    run.add_argument("--dry-run", action="store_true", help="Skip Vikunja calls and file moves")
    return parser


def _select(container: Container, only: Path | None) -> list[Screenshot]:
    if only is None:
        return container.source.list()
    import mimetypes

    return [Screenshot(path=only, mime_type=mimetypes.guess_type(only)[0] or "image/png")]


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    settings = Settings()
    configure_logging(settings)
    container = Container(settings)

    try:
        match args.command:
            case "read":
                for shot in container.source.list():
                    print(shot.path)
            case "analyze":
                for shot in _select(container, args.file):
                    print(shot.path.name, container.analyzer.analyze(shot).model_dump_json(indent=2))
            case "map":
                for shot in _select(container, args.file):
                    for task in container.analyzer.analyze(shot).tasks:
                        req = container.mapper.to_request(task)
                        print(f"PUT /projects/{req.project_id}/tasks", req.model_dump_json(exclude_none=True))
            case "run":
                result = container.pipeline.run(dry_run=args.dry_run)
                return 1 if result.failed else 0
    except DomainError:
        _log.exception("Command %s failed", args.command)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
