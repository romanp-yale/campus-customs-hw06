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
    from html_layout import rendered_html
    soup = BeautifulSoup(raw, 'html.parser')
    excluded = []
    for comment in soup.find_all(string=lambda node: isinstance(node, Comment)):
        excluded.append({'reason': 'HTML comment', 'text': str(comment)[:500]})
        comment.extract()
    # Prevent refresh/navigation and scripts before handing content to the offline renderer.
    for tag in list(soup.find_all(['script', 'iframe', 'object', 'embed'])):
        tag.decompose()
    for tag in soup.find_all('meta', attrs={'http-equiv': True}):
        if tag.get('http-equiv', '').lower() == 'refresh':
            tag.decompose()
    rendered = rendered_html(str(soup))
    return PreparedDocument(rendered['text'], excluded + rendered['excluded'],
                            ['Offline browser layout at 1280px; vendor scripts and external resources disabled.'])


def visible_pdf(path: Path) -> PreparedDocument:
    lines, excluded = [], []
    with pymupdf.open(path) as document:
        for number, page in enumerate(document, 1):
            pixmap = page.get_pixmap(colorspace=pymupdf.csRGB, alpha=False)
            # Only a simple, fully opaque rectangle is sufficient proof of coverage.
            # Bounding boxes of arbitrary paths are not equivalent to filled coverage.
            covers = [drawing for drawing in page.get_drawings()
                      if drawing.get('fill') is not None and drawing.get('fill_opacity', 0) >= .99
                      and len(drawing['items']) == 1 and drawing['items'][0][0] == 're']
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
                elif any(drawing['seqno'] > span['seqno'] and drawing['items'][0][1].contains(box)
                         for drawing in covers):
                    reason = 'Text covered by later opaque rectangle'
                elif any(drawing['seqno'] > span['seqno'] and drawing['items'][0][1].intersects(box)
                         for drawing in covers):
                    reason = 'Partially covered text requires human review'
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
    return PreparedDocument('\n'.join(lines), excluded,
                            ['No OCR; opaque rectangular coverage checked; complex paths/images/clipping remain heuristic.'])


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


@dataclass
class QuoteValidation:
    facts: dict
    evidence: dict
    issues: list[str]

    @property
    def needs_human_review(self):
        return bool(self.issues)


def validate_quote(path: Path, text: str) -> QuoteValidation:
    """Primary quote heading/labels only, never handbook usual-vendor inference."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    vendor = None
    if path.suffix.lower() in ('.html', '.htm'):
        headings = BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser').find_all('h1')
        visible_headings = {heading.get_text(' ', strip=True) for heading in headings
                            if heading.get_text(' ', strip=True) in text}
        if len(visible_headings) == 1:
            vendor = visible_headings.pop()
    elif path.suffix.lower() == '.pdf':
        vendor = lines[0] if lines else None
    elif path.suffix.lower() == '.eml':
        vendor = lines[-1] if lines else None
    evidence, issues = {}, []
    def value(name, pattern, transform):
        matches = list(re.finditer(pattern, text, flags=re.I | re.M))
        evidence[name] = [{'value': transform(match.group(1)), 'line': text[:match.start()].count('\n') + 1,
                           'source': match.group(0).strip()} for match in matches]
        distinct = {entry['value'] for entry in evidence[name]}
        if len(distinct) != 1:
            issues.append(f'{name}: conflicting visible primary labels' if distinct else f'{name}: no usable primary label')
            return None
        return distinct.pop()
    # An SKU in an instruction, tracking link, or other free text is not a primary field.
    # Allow the existing baseline HTML reader's label/value concatenation as well.
    sku_pattern = r'^\s*(?:Campus Customs\s+)?SKU\s*:?\s*(CC-[A-Z]{2}-\d{3})\b'
    sku = value('sku', sku_pattern, str.upper) if re.search(sku_pattern, text, re.I | re.M) else value(
        'sku', r'^\s*(?:Item\s*:[^\n]*?|Happy to quote[^\n]*?|Quote for[^\n]*?)\((CC-[A-Z]{2}-\d{3})\)', str.upper)
    facts = {'vendor': vendor, 'sku': sku,
             'unit_price': value('unit_price', r'^\s*Unit price\s*:?\s*\$((?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)(?![\w,.])', lambda value: float(value.replace(',', ''))),
             'lead_time_days': value('lead_time_days', r'^\s*Lead time\s*:?\s*(\d+)\s*(?:business\s+)?days', int),
             'min_order': value('min_order', r'^\s*Minimum order\s*:?\s*((?:\d{1,3}(?:,\d{3})+)|\d+)\s*units', lambda value: int(value.replace(',', '')))}
    evidence['vendor'] = [{'value': vendor, 'source': 'Primary visible heading or email signature'}]
    if vendor is None:
        issues.append('vendor: no unambiguous primary heading/signature')
    return QuoteValidation(facts, evidence, issues)


def anchored_facts(path: Path, text: str) -> dict:
    return validate_quote(path, text).facts


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
