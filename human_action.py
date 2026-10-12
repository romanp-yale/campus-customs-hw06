"""Explicit human-only log simulation; never callable from a vendor document."""
import argparse
import json
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from tools import DeskDeps, approve_payment, send_email


def main():
    parser = argparse.ArgumentParser(description='Human-authorized simulated action; no real emails or payments')
    parser.add_argument('--tool', choices=('send_email', 'approve_payment'), required=True)
    parser.add_argument('--arguments-json', type=Path, required=True)
    args = parser.parse_args()
    arguments = json.loads(args.arguments_json.read_text(encoding='utf-8'))
    print('Proposed LOG-ONLY action:', args.tool, json.dumps(arguments, indent=2))
    if input('Type AUTHORIZE to approve these exact arguments for this one simulated action: ') != 'AUTHORIZE':
        raise SystemExit('Not authorized; no simulated action executed')
    deps = DeskDeps(Path('human-only'), str(uuid4()), layers=frozenset({'design'}),
                    human_authorization={'tool': args.tool, 'arguments': arguments})
    ctx = SimpleNamespace(deps=deps)
    print({'send_email': send_email, 'approve_payment': approve_payment}[args.tool](ctx, **arguments))


if __name__ == '__main__':
    main()
