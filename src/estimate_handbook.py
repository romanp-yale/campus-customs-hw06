"""Reproduce Problem 2 locally; no model calls or credentials required."""
from decimal import Decimal
from importlib.metadata import version
from pathlib import Path
import hashlib
import json

import tiktoken

ROOT = Path(__file__).resolve().parents[1]


def main():
    raw = (ROOT / 'data/shop_handbook.md').read_bytes()
    text = raw.decode('utf-8')  # Preserve original newlines and all Markdown.
    tokens = len(tiktoken.get_encoding('o200k_base').encode_ordinary(text))
    pricing = json.loads((ROOT / 'data/prices.json').read_text(encoding='utf-8'),
                         parse_float=Decimal)['gpt-6-luna']
    print(f'tiktoken version: {version("tiktoken")}')
    print(f'Encoding: o200k_base; tokens: {tokens}; characters: {len(text)}')
    print(f'Handbook SHA-256: {hashlib.sha256(raw).hexdigest()}')
    for calls in (1, 1000):
        for label, key in [('uncached', 'input_per_1m'),
                           ('fully cached', 'cached_input_per_1m')]:
            rate = pricing[key]
            cost = Decimal(tokens) * calls * rate / Decimal(1_000_000)
            print(f'{calls} call(s), {label}: {tokens} * {calls} / 1000000 * {rate} = ${cost:.8f}')


if __name__ == '__main__':
    main()
