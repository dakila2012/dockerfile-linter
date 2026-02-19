import argparse
import sys
import json
from src.linter import lint
def main():
    parser = argparse.ArgumentParser(
        description='CLI tool to lint Dockerfiles for common best practices and errors.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --help
  %(prog)s Dockerfile
  %(prog)s -
        """
    )
    parser.add_argument(
        'dockerfile',
        nargs='?',
        default='-',
        help='Path to Dockerfile or "-" to read from stdin'
    )
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 0.1.0'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output issues in JSON format'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Only return exit code, no output'
    )
    args = parser.parse_args()
    if args.dockerfile == '-':
        content = sys.stdin.read()
        dockerfile_name = args.dockerfile
    else:
        try:
            with open(args.dockerfile, 'r', encoding='utf-8') as f:
                content = f.read()
            dockerfile_name = args.dockerfile
        except FileNotFoundError:
            print(f"Error: {args.dockerfile}: No such file or directory", file=sys.stderr)
            sys.exit(2)
        except Exception as e:
            print(f"Error reading {args.dockerfile}: {e}", file=sys.stderr)
            sys.exit(2)
    issues = lint(content)
    issues.sort(key=lambda x: x[0])
    if args.quiet:
        sys.exit(1 if issues else 0)
    elif args.json:
        output = []
        for line_num, msg in issues:
            issue = {"message": msg}
            if line_num != 0:
                issue["line"] = line_num
            issue["file"] = dockerfile_name
            output.append(issue)
        print(json.dumps(output))
        sys.exit(1 if issues else 0)
    else:
        for line_num, msg in issues:
            if line_num == 0:
                print(f"{dockerfile_name}: global: {msg}")
            else:
                print(f"{dockerfile_name}:{line_num}: {msg}")
        sys.exit(1 if issues else 0)
if __name__ == "__main__":
    main()
