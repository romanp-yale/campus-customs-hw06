"""Offline, script-disabled HTML visibility inspection in a fresh headless browser."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import os


READ_VISIBLE_TEXT = r"""() => {
    const kept = [], excluded = [];
    const walker = document.createTreeWalker(document.body, 4);
    let node;
    while ((node = walker.nextNode())) {
        const text = node.nodeValue.trim();
        if (!text) continue;
        const el = node.parentElement;
        if (!el || el.closest('script,style,noscript,template,iframe,object,embed,svg,canvas')) continue;
        let reason = null;
        for (let ancestor = el; ancestor; ancestor = ancestor.parentElement) {
            const style = getComputedStyle(ancestor);
            if (style.display === 'none' || style.visibility === 'hidden' || style.visibility === 'collapse') reason = 'Rendered hidden HTML';
            if (Number(style.opacity) <= .01) reason = 'Rendered transparent HTML';
        }
        const style = getComputedStyle(el);
        if (parseFloat(style.fontSize) < 3) reason = 'Rendered HTML microtext';
        const range = document.createRange();
        range.selectNodeContents(node);
        const rect = range.getBoundingClientRect();
        // Do not discard normal content below the fold or horizontally scrollable content.
        if (rect.right <= 0 || rect.bottom <= 0) reason = 'Rendered text entirely left of or above document origin';
        if (rect.width === 0 || rect.height === 0) reason = reason || 'No rendered text area';
        const rgba = value => (value.match(/[\d.]+/g) || []).map(Number);
        const foreground = rgba(style.color);
        let background = [255,255,255,1];
        for (let ancestor = el; ancestor; ancestor = ancestor.parentElement) {
            const color = rgba(getComputedStyle(ancestor).backgroundColor);
            if (color.length >= 3 && (color.length < 4 || color[3] >= .99)) { background = color; break; }
        }
        if (foreground.length >= 3 && foreground.slice(0,3).every((c,i) => Math.abs(c-background[i]) < 3)) reason = 'Rendered text matches background';
        if (foreground.length === 4 && foreground[3] <= .01) reason = 'Rendered transparent text color';
        if (reason) excluded.push({reason, text:text.slice(0,500), bounds:{left:rect.left,right:rect.right,top:rect.top,bottom:rect.bottom}});
        else kept.push(text);
    }
    return {text:kept.join('\n'), excluded};
}"""


def _render(raw):
    from playwright.sync_api import sync_playwright
    executable = os.getenv('CAMPUS_HTML_BROWSER', '').strip()
    if not executable:
        for candidate in (r'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
                          r'C:/Program Files/Google/Chrome/Application/chrome.exe'):
            if Path(candidate).is_file():
                executable = candidate
                break
    with sync_playwright() as runtime:
        options = {'headless': True}
        if executable:
            options['executable_path'] = executable
        browser = runtime.chromium.launch(**options)
        try:
            context = browser.new_context(java_script_enabled=False, offline=True,
                                          service_workers='block', accept_downloads=False,
                                          viewport={'width': 1280, 'height': 900})
            context.route('**/*', lambda route: route.abort())
            page = context.new_page()
            page.set_content(raw, wait_until='domcontentloaded', timeout=15000)
            return page.evaluate(READ_VISIBLE_TEXT)
        finally:
            browser.close()


def rendered_html(raw):
    # PydanticAI runs inside asyncio. Keep the synchronous renderer in its own
    # worker thread rather than using Playwright's sync API on that event loop.
    with ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(_render, raw).result(timeout=30)
