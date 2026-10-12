"""Actual offline file:// browser validation in a directory containing only HTML."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from tools import ROOT


def main():
    html = ROOT / 'output/hw6_report.html'
    raw = html.read_text(encoding='utf-8')
    soup = BeautifulSoup(raw, 'html.parser')
    assert not soup.find_all('script', src=True) and not soup.find_all('link')
    assert all(image['src'].startswith('data:') for image in soup.find_all('img'))
    assert all(anchor.get('href', '').startswith('#') for anchor in soup.find_all('a'))
    data = json.loads(soup.find('script', id='report-data').string)
    assert len(data['exam']) == 10
    assert '__DATA__' not in raw and '__CACHE_' not in raw
    previews = ROOT / 'output/hw6_report_previews'
    previews.mkdir(exist_ok=True)
    executable = next((str(p) for p in (Path('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'),
                                       Path('C:/Program Files/Google/Chrome/Application/chrome.exe')) if p.is_file()), None)
    errors, requests, checks = [], [], {}
    with tempfile.TemporaryDirectory(prefix='hw6-report-offline-') as isolated:
        copy = Path(isolated) / 'report.html'
        shutil.copyfile(html, copy)
        assert len(list(Path(isolated).iterdir())) == 1
        with sync_playwright() as runtime:
            browser = runtime.chromium.launch(headless=True, **({'executable_path': executable} if executable else {}))
            try:
                context = browser.new_context(offline=True, viewport={'width': 1440, 'height': 1000}, accept_downloads=True, reduced_motion='reduce')
                context.route('**/*', lambda route: route.abort() if not route.request.url.startswith('file:') else route.continue_())
                page = context.new_page()
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.on('request', lambda request: requests.append(request.url))
                page.goto(copy.as_uri(), wait_until='load')
                assert page.title() == 'Campus Customs · Vendor Desk Results'
                assert page.locator('#exam-body>tr').count() == 10
                assert page.locator('svg').count() == 2
                assert page.locator('.attack-card').count() == 4
                assert page.locator('#monthly-cached').inner_text() == '$11.14'
                assert page.locator('#monthly-zero').inner_text() == '$84.40'
                checks['initial_content_charts_tables'] = True
                page.screenshot(path=str(previews / 'desktop_overview.png'), full_page=False)
                page.get_by_role('link', name='Security', exact=True).click()
                assert 80 <= page.locator('#security').bounding_box()['y'] <= 130
                checks['section_navigation_and_sticky_header_offset'] = True
                page.locator('#exam-filter').select_option('review')
                assert page.locator('#exam-body>tr:visible').count() == 2
                assert '2 of 10' in page.locator('#exam-status').inner_text()
                page.locator('#exam-filter').select_option('recommend')
                assert page.locator('#exam-body>tr:visible').count() == 4
                page.locator('#exam-filter').select_option('all')
                page.locator('#exam-search').fill('e08')
                assert page.locator('#exam-body>tr:visible').count() == 1
                assert 'Unknown' in page.locator('#exam-body>tr:visible').inner_text()
                page.locator('#exam-search').fill('not-a-vendor')
                assert page.locator('#exam-body>tr:visible').count() == 0
                assert '0 of 10' in page.locator('#exam-status').inner_text()
                page.locator('#exam-search').fill('')
                checks['exam_filters_and_empty_search'] = True
                first = page.locator('#exam-body>tr').first.locator('details')
                first.locator('summary').click()
                assert first.evaluate('(element)=>element.open')
                assert data['exam'][0]['reason'] in first.inner_text()
                first.locator('summary').click()
                checks['decision_reason_expansion'] = True
                page.locator('#volume').evaluate("element=>{element.value='2000';element.dispatchEvent(new Event('input',{bubbles:true}));}")
                assert page.locator('#monthly-volume').inner_text() == '60,000'
                assert page.locator('#monthly-cached').inner_text() == '$22.27'
                page.locator('#volume').evaluate("element=>{element.value='1000';element.dispatchEvent(new Event('input',{bubbles:true}));}")
                page.locator('#projection-source').select_option('final')
                assert page.locator('#monthly-cached').inner_text() == '$13.83'
                assert page.locator('#monthly-zero').inner_text() == '$83.93'
                assert 'no causal savings percentage' in page.locator('#projection-note').inner_text()
                page.locator('#projection-source').select_option('baseline')
                checks['projection_volume_and_cohort_controls'] = True
                with page.expect_download() as info:
                    page.locator('#export-exam').click()
                download = info.value
                assert json.loads(Path(download.path()).read_text(encoding='utf-8')) == data['exam']
                checks['json_download_matches_unedited_exam_results'] = True
                # Test the print button without opening an OS dialog.
                page.evaluate('window.print=()=>{window.printInvoked=true;}')
                page.locator('#print-report').click()
                assert page.evaluate('window.printInvoked') is True
                checks['print_control_wiring'] = True
                page.locator('#cost').screenshot(path=str(previews / 'cost_chart.png'), style='.topbar{visibility:hidden}')
                page.locator('#security').screenshot(path=str(previews / 'security_chart.png'), style='.topbar{visibility:hidden}')
                page.locator('#defenses').screenshot(path=str(previews / 'defense_overhead.png'), style='.topbar{visibility:hidden}')
                page.locator('#redteam').screenshot(path=str(previews / 'red_team.png'), style='.topbar{visibility:hidden}')
                page.locator('#exam').screenshot(path=str(previews / 'exam_table.png'), style='.topbar{visibility:hidden}')
                page.locator('.screenshot').last.locator('summary').click()
                assert page.locator('.screenshot').last.locator('img').evaluate('(image)=>image.complete&&image.naturalWidth>0')
                page.locator('.screenshot').last.locator('summary').click()
                checks['embedded_rendering_preview'] = True
                for width in (1280, 1024, 768, 640):
                    page.set_viewport_size({'width': width, 'height': 960})
                    page.evaluate('window.scrollTo(0,0)')
                    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1')
                    if width in (1024, 768):
                        page.screenshot(path=str(previews / f'overview_{width}.png'))
                checks['responsive_page_no_horizontal_overflow'] = [1440, 1280, 1024, 768, 640]
                page.emulate_media(media='print')
                assert page.locator('.topbar').evaluate('(e)=>getComputedStyle(e).position') == 'static'
                checks['print_styles'] = True
                context.close()
                nojs = browser.new_context(offline=True, java_script_enabled=False, viewport={'width': 1280, 'height': 960})
                plain = nojs.new_page()
                plain.goto(copy.as_uri(), wait_until='load')
                assert plain.locator('#exam-body>tr').count() == 10 and plain.locator('svg').count() == 2
                checks['static_report_without_javascript'] = True
                nojs.close()
            finally:
                browser.close()
    external = [url for url in requests if not url.startswith(('file:', 'data:', 'blob:'))]
    assert not errors and not external
    results = {'html_sha256': hashlib.sha256(html.read_bytes()).hexdigest(), 'isolated_directory_only_html': True,
               'browser': 'Headless Edge/Chromium', 'network_offline': True, 'external_resource_requests': external,
               'javascript_errors': errors, 'checks': checks, 'screenshots': str(previews.relative_to(ROOT)),
               'visual_inspection': 'Pending screenshot review; print dialog was stubbed, not physically printed.'}
    (ROOT / 'output/hw6_report_browser_test.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
    print('Offline file:// checks passed: filters, projections, download, embedded images, charts, print control and responsive widths.')


if __name__ == '__main__':
    main()
