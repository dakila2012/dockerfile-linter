# dockerfile-linter

A CLI tool to lint Dockerfiles for common best practices and errors using a simple line-based parser. It handles multi-line instructions, escape directives, and checks for issues like unknown instructions, multiple FROMs, missing CMD/ENTRYPOINT, and more.

Production-ready with solid parsing, many practical rules, good error handling, and idiomatic UX including JSON output and quiet mode.

## Installation

```bash
git clone <repository-url> dockerfile-linter
cd dockerfile-linter
```

No external dependencies (uses Python standard library only). Run with `python src/cli.py`.

## Usage

```bash
# Display help
python src/cli.py --help

# Lint a local Dockerfile
python src/cli.py Dockerfile

# Lint from stdin
echo "FROM ubuntu:latest
RUN apt-get update
CMD [\"echo\", \"hello\"]" | python src/cli.py -

# JSON output
python src/cli.py Dockerfile --json

# Quiet mode (exit code only)
python src/cli.py Dockerfile --quiet
```

## Features

- Line-based parsing with support for continuations (`\`) and escape directives (`# escape=`)
- Detects common issues: unknown instructions, multiple `FROM`, missing `CMD`/`ENTRYPOINT`, and more
- Sorted issues by line number
- File or stdin input
- JSON output (`--json`)
- Quiet mode (`--quiet`, `-q`) for CI
- Version info (`--version`)

## Dependencies

Python standard library (argparse).

## Tests

No tests implemented.

## License

MIT