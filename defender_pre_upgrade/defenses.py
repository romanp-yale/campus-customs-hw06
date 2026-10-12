"""Local visibility filtering, source anchoring, and trusted handbook policy.

No answer-key access, network calls, or model calls exist in this module.
"""
from dataclasses import dataclass, field
from decimal import Decimal
from email import policy
from email.parser import BytesParser
from pathlib import Path
import re
import unicodedata

from bs4 import BeautifulSoup, Comment
import pymupdf
import tinycss2

from models import VendorRecommendation


def parse_layers(value: str) -> frozenset[str]:
    layers = frozenset(('code', 'design', 'prompt')) if value == 'all' else (
        frozenset() if value == 'none' else frozenset(value.split(',')))
    if not layers <= {'code', 'design', 'prompt'}:
        raise ValueError('Defense layers must be none, all, or a comma-separated subset of code,design,prompt')
    return layers


@dataclass
class PreparedDocument:
    text: str
    excluded: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def declarations(source):
    return {item.lower_name: tinycss2.serialize(item.value).strip().lower()
            for item in tinycss2.parse_declaration_list(source, skip_comments=True, skip_whitespace=True)
            if item.type == 'declaration'}


def visible_html(raw: str) -> PreparedDocument:
    soup = BeautifulSoup(raw, 'html.parser')
    excluded = []
    rules = []
    for style in soup.find_all('style'):
        for rule in tinycss2.parse_stylesheet(style.get_text(), skip_comments=True, skip_whitespace=True):
            if rule.type == 'qualified-rule':
                rules.append((tinycss2.serialize(rule.prelude).strip(), declarations(rule.content)))
    styles = {}
    for selector, properties in rules:
        try:
            for tag in soup.select(selector):
                styles.setdefault(id(tag), {}).update(properties)
        except Exception:
            pass  # Unsupported selectors do not authorize treating text as trusted.
    for tag in soup.find_all(True):
        styles.setdefault(id(tag), {}).update(declarations(tag.get('style', '')))
    for comment in soup.find_all(string=lambda node: isinstance(node, Comment)):
        excluded.append({'reason': 'HTML comment', 'text': str(comment)[:500]})
        comment.extract()
    for tag in list(soup.find_all(True)):
        if tag.name is None or tag.attrs is None:
            continue
        if tag.name in {'head', 'script', 'style', 'noscript', 'template', 'iframe', 'object', 'embed', 'svg', 'canvas'}:
            tag.decompose()
            continue
        properties = styles.get(id(tag), {})
        reason = None
        if tag.has_attr('hidden') or properties.get('display') == 'none' or properties.get('visibility') in ('hidden', 'collapse'):
            reason = 'CSS/HTML hidden'
        elif properties.get('opacity') in ('0', '0.0'):
            reason = 'Transparent HTML'
        elif re.fullmatch(r'0+(?:\.0+)?(?:px|pt|em|rem|%)?', properties.get('font-size', '')):
            reason = 'Zero-size HTML text'
        elif re.fullmatch(r'[012](?:\.\d+)?(?:px|pt)', properties.get('font-size', '')):
            reason = 'HTML microtext below 3px/pt'
        inherited = {}
        for ancestor in reversed([tag, *list(tag.parents)]):
            inherited.update(styles.get(id(ancestor), {}))
        white = {'white', '#fff', '#ffffff', 'rgb(255,255,255)', 'rgb(255, 255, 255)'}
        foreground = inherited.get('color', '').strip()
        background = inherited.get('background-color', inherited.get('background', 'white')).strip()
        if foreground in white and background in white:
            reason = 'White HTML text on white background'
        if reason:
            excluded.append({'reason': reason, 'text': tag.get_text(' ', strip=True)[:500]})
            tag.decompose()
    # Preserve real quote text and legitimate correction prose; do not blacklist "ignore".
    text = soup.get_text('\n', strip=True)
    return PreparedDocument(text, excluded, ['Static CSS subset; no JavaScript, external stylesheets, or full layout engine.'])


def visible_pdf(path: Path) -> PreparedDocument:
    lines, excluded = [], []
    with pymupdf.open(path) as document:
        for number, page in enumerate(document, 1):
            pixmap = page.get_pixmap(colorspace=pymupdf.csRGB, alpha=False)
            for span in page.get_texttrace():
                text = ''.join(chr(char[0]) for char in span['chars'])
                box = pymupdf.Rect(span['bbox'])
                reason = None
                if not page.rect.contains(box):
                    reason = 'Text outside page bounds'
                elif span['size'] < 3:
                    reason = 'PDF microtext below 3 points'
                elif span.get('opacity', 1) <= 0.01 or span.get('type', 0) > 1:
                    reason = 'Invisible PDF text rendering'
                else:
                    color = span.get('color', (0, 0, 0))
                    if not isinstance(color, (tuple, list)):
                        color = (color,) * 3
                    # Sample the rendered background above/below the span, retaining white-on-dark text.
                    samples = []
                    for px, py in ((box.x0, box.y0 - 2), (box.x0, box.y1 + 2), (box.x1, box.y1 + 2)):
                        px, py = int(px), int(py)
                        if 0 <= px < pixmap.width and 0 <= py < pixmap.height:
                            samples.append(pixmap.pixel(px, py))
                    if len(color) == 3 and min(color) > .95 and samples and all(min(sample[:3]) > 245 for sample in samples):
                        reason = 'White PDF text on rendered white background'
                if reason:
                    excluded.append({'page': number, 'reason': reason, 'text': text[:500], 'bbox': list(box), 'font_size': span['size']})
                elif text.strip():
                    lines.append(text)
    return PreparedDocument('\n'.join(lines), excluded, ['No OCR; sampled background is a heuristic and does not cover every overlay or clipping case.'])


def prepare_document(path: Path) -> PreparedDocument:
    suffix = path.suffix.lower()
    if suffix in ('.html', '.htm'):
        prepared = visible_html(path.read_text(encoding='utf-8'))
    elif suffix == '.pdf':
        prepared = visible_pdf(path)
    elif suffix == '.eml':
        message = BytesParser(policy=policy.default).parsebytes(path.read_bytes())
        body = message.get_body(preferencelist=('plain', 'html'))
        if body is None:
            raise ValueError('No readable email body')
        prepared = visible_html(body.get_content()) if body.get_content_type() == 'text/html' else PreparedDocument(body.get_content())
        prepared.text = '\n'.join(f'{name}: {message.get(name, "")}' for name in ('From', 'To', 'Date', 'Subject')) + '\n\n' + prepared.text
        prepared.warnings.append('Email attachments and alternative bodies are not merged; plain text preferred when present.')
    else:
        raise ValueError('Supported document types: HTML, PDF, .eml')
    controls = '\u200b\u200c\u200d\u2060\ufeff\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069'
    if any(char in prepared.text for char in controls):
        prepared.excluded.append({'reason': 'Zero-width or bidi control characters', 'text': 'Formatting controls normalized; visible wording retained.'})
        prepared.text = prepared.text.translate({ord(char): None for char in controls})
    prepared.text = unicodedata.normalize('NFC', prepared.text)
    if not prepared.text.strip():
        raise ValueError('Document has no readable visible text; needs human review/OCR')
    return prepared


def anchored_facts(path: Path, text: str) -> dict:
    """Primary quote heading/labels only, never handbook usual-vendor inference."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    vendor = None
    if path.suffix.lower() in ('.html', '.htm'):
        headings = BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser').find_all('h1')
        if len(headings) == 1:
            heading = headings[0].get_text(' ', strip=True)
            vendor = heading if heading in text else None
    elif path.suffix.lower() == '.pdf':
        vendor = lines[0] if lines else None
    elif path.suffix.lower() == '.eml':
        vendor = lines[-1] if lines else None
    def value(pattern, transform):
        found = re.findall(pattern, text, flags=re.I)
        distinct = {transform(item) for item in found}
        return distinct.pop() if len(distinct) == 1 else None
    return {'vendor': vendor,
            'sku': value(r'\b(CC-[A-Z]{2}-\d{3})\b', str.upper),
            'unit_price': value(r'(?m)^\s*Unit price\s*:?\s*\$([0-9]+(?:\.[0-9]+)?)', float),
            'lead_time_days': value(r'(?m)^\s*Lead time\s*:?\s*(\d+)\s*(?:business\s+)?days', int),
            'min_order': value(r'(?m)^\s*Minimum order\s*:?\s*(\d+)\s*units', int)}


def handbook_policy(facts: dict, handbook: str) -> VendorRecommendation:
    """Rules and catalogue come from the trusted handbook, never document/model commands."""
    approved_section = handbook.split('## 5. Approved vendors', 1)[1].split('## 6.', 1)[0]
    approved = {cells[1] for line in approved_section.splitlines()
                if line.startswith('|') and len(cells := [cell.strip() for cell in line.strip('|').split('|')]) >= 3
                and cells[0] not in ('Code', '---')}
    catalogue = {}
    for line in handbook.splitlines():
        if line.startswith('| CC-'):
            cells = [cell.strip() for cell in line.strip('|').split('|')]
            catalogue[cells[0]] = Decimal(cells[4].removeprefix('$'))
    failures = []
    rules = handbook.split('## 4. Purchasing rules', 1)[1].split('## 5.', 1)[0]
    lead_limit = int(re.search(r'lead time is (\d+) days', rules).group(1))
    order_limit = int(re.search(r'minimum order is (\d+) units', rules).group(1))
    if facts['vendor'] not in approved:
        failures.append('vendor is unknown or not approved')
    maximum = catalogue.get(facts['sku'])
    if maximum is None:
        failures.append('SKU is unknown or absent from the catalogue')
    if facts['unit_price'] is None:
        failures.append('unit price is unknown')
    elif maximum is not None and Decimal(str(facts['unit_price'])) > maximum:
        failures.append('unit price exceeds the catalogue maximum')
    if facts['lead_time_days'] is None or facts['lead_time_days'] > lead_limit:
        failures.append(f'lead time is unknown or exceeds {lead_limit} days')
    if facts['min_order'] is None or facts['min_order'] > order_limit:
        failures.append(f'minimum order is unknown or exceeds {order_limit} units')
    explanation = ('Do not recommend because ' + '; '.join(failures) + '.') if failures else (
        'Recommend because the vendor is approved, the SKU and unit price meet catalogue rules, and lead time and minimum order meet handbook limits.')
    return VendorRecommendation(**facts, decision='do_not_recommend' if failures else 'recommend', explanation=explanation)
