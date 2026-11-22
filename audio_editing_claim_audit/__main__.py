import argparse
import json
import sys
from . import __version__
from .audit import audit

class Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(1, f'{self.prog}: error: {message}\n')

def main():
    parser = Parser(prog='audio-editing-claim-audit')
    parser.add_argument('--version', action='version', version=__version__)
    sub = parser.add_subparsers(dest='command', required=True, parser_class=Parser)
    run = sub.add_parser('audit')
    run.add_argument('repo', nargs='?', default='.')
    run.add_argument('--json', action='store_true')
    run.add_argument('--verbose', action='store_true')
    run.add_argument('--ignore', action='append', default=[])
    run.add_argument('--fail-on', choices=('high', 'medium'), default='high')
    args = parser.parse_args()
    try:
        findings = audit(args.repo, args.ignore)
    except (OSError, UnicodeError) as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 1
    failed = any(f['severity'] == 'HIGH' or args.fail_on == 'medium' for f in findings)
    if args.json:
        print(json.dumps({'status': 'FAIL' if failed else 'PASS', 'findings': findings}, indent=2))
    else:
        print('FAIL' if failed else 'PASS')
        for finding in findings: print(f"{finding['severity']}: {finding['id']}")
        if args.verbose: print(f'Inspected: {args.repo}')
    return 2 if failed else 0

if __name__ == '__main__':
    sys.exit(main())
