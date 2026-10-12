"""Actual browser screenshots and source-versus-paint evidence; no AI calls."""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
from defenses import prepare_document, validate_quote
from tools import ROOT, extract_document, timestamp


def main():
    cases = json.loads((ROOT / 'output/red_team_round2_cases.json').read_text())['cases']
    folder = ROOT / 'output/red_team_round2_previews'
    folder.mkdir(exist_ok=True)
    results = {'timestamp': timestamp(), 'method': 'Actual Chromium browser paint, vendor JS disabled, offline and all resource requests aborted', 'documents': []}
    executable = next((str(p) for p in (Path('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'),
                                       Path('C:/Program Files/Google/Chrome/Application/chrome.exe')) if p.is_file()), None)
    with sync_playwright() as runtime:
        browser = runtime.chromium.launch(headless=True, **({'executable_path': executable} if executable else {}))
        try:
            for name in cases:
                path = ROOT / 'data/my_attacks' / name
                context = browser.new_context(java_script_enabled=False, offline=True, viewport={'width': 1280, 'height': 960}, service_workers='block')
                context.route('**/*', lambda route: route.abort())
                page = context.new_page()
                page.set_content(path.read_text(encoding='utf-8'), wait_until='domcontentloaded')
                page.screenshot(path=str(folder / (path.stem + '.png')), full_page=True)
                paint_details = page.evaluate('''() => {
                    const price = document.querySelector('#quoted-price');
                    const clip = document.querySelector('#approval-attestation');
                    const note = document.querySelector('#review-normalization');
                    return {price_dom:price?.textContent, price_after:price ? getComputedStyle(price,'::after').content : null,
                            clip_path:clip ? getComputedStyle(clip).clipPath : null,
                            note_after:note ? getComputedStyle(note,'::after').content : null};
                }''')
                context.close()
                baseline = extract_document(path)
                defended = prepare_document(path)
                (folder / (path.stem + '_baseline.txt')).write_text(baseline, encoding='utf-8')
                (folder / (path.stem + '_defended.txt')).write_text(defended.text, encoding='utf-8')
                validation = validate_quote(path, defended.text)
                results['documents'].append({'document': name, 'screenshot': str((folder / (path.stem + '.png')).relative_to(ROOT)),
                                             'computed_paint_details': paint_details,
                                             'payload_in_baseline': ' '.join(cases[name]['payload'].split()) in ' '.join(baseline.split()),
                                             'payload_in_defended': ' '.join(cases[name]['payload'].split()) in ' '.join(defended.text.split()),
                                             'source_anchors': validation.facts, 'validation_issues': validation.issues,
                                             'excluded': defended.excluded, 'human_visual_review': 'Pending image inspection'})
        finally:
            browser.close()
    (ROOT / 'output/red_team_round2_rendering.json').write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
    print('Two actual browser screenshots and exact reader inputs saved.')


if __name__ == '__main__':
    main()
