"""Offline, script-disabled HTML visibility inspection in a fresh headless browser."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import os


READ_VISIBLE_TEXT = r"""() => {
    const kept = [], excluded = [], emitted = new Set();
    const rgba = value => (value.match(/[\d.]+/g) || []).map(Number);
    // A small, explicit paint case: a generated-text pseudo-element with an
    // opaque background, positive stacking order and full-parent inset cover.
    // Do not infer coverage from arbitrary polygons, images or gradients.
    const replacement = el => {
        for (const pseudo of ['::after','::before']) {
            const s = getComputedStyle(el,pseudo);
            const bg = rgba(s.backgroundColor);
            if (s.position !== 'absolute' || !['top','right','bottom','left'].every(side => /^-?[\d.]+px$/.test(s[side]) && parseFloat(s[side]) <= 0)
                || s.zIndex === 'auto' || Number(s.zIndex) < 1 || Number(s.opacity) < .99
                || bg.length < 3 || (bg.length === 4 && bg[3] < .99) || s.backgroundImage !== 'none'
                || s.visibility !== 'visible' || s.transform !== 'none' || s.clipPath !== 'none') continue;
            try {
                const value = JSON.parse(s.content);
                const fg=rgba(s.color);
                const readable=parseFloat(s.fontSize)>=3 && !(fg.length===4 && fg[3]<=.01)
                    && !fg.slice(0,3).every((c,i)=>Math.abs(c-bg[i])<3);
                if (typeof value === 'string') return {text:readable?value.trim():null, pseudo};
            } catch (_) { /* Unsupported CSS content syntax is not guessed. */ }
        }
        return null;
    };
    const emptyInset = (style, el) => {
        const match = /^inset\(([^)]+)\)$/.exec(style.clipPath);
        if (!match || match[1].includes('round')) return false;
        const parts=match[1].trim().split(/\s+/);
        if (!parts.every(p=>/^[\d.]+(?:px|%)$/.test(p))) return false;
        const [a,b=a,c=a,d=b]=parts, box=el.getBoundingClientRect();
        const length=(v,total)=>parseFloat(v)*(v.endsWith('%')?total/100:1);
        return length(a,box.height)+length(c,box.height)>=box.height
            || length(b,box.width)+length(d,box.width)>=box.width;
    };
    const walker = document.createTreeWalker(document.body, 4);
    let node;
    while ((node = walker.nextNode())) {
        const text = node.nodeValue.trim();
        if (!text) continue;
        const el = node.parentElement;
        if (!el || el.closest('script,style,noscript,template,iframe,object,embed,svg,canvas')) continue;
        let reason = null;
        let painted = null, paintedElement = null;
        for (let ancestor = el; ancestor; ancestor = ancestor.parentElement) {
            const style = getComputedStyle(ancestor);
            if (style.display === 'none' || style.visibility === 'hidden' || style.visibility === 'collapse') reason = 'Rendered hidden HTML';
            if (Number(style.opacity) <= .01) reason = 'Rendered transparent HTML';
            if (emptyInset(style, ancestor)) reason = 'Rendered empty CSS inset clip';
            const candidate = replacement(ancestor);
            if (candidate) { painted=candidate; paintedElement=ancestor; }
        }
        const style = getComputedStyle(el);
        if (parseFloat(style.fontSize) < 3) reason = 'Rendered HTML microtext';
        const range = document.createRange();
        range.selectNodeContents(node);
        const rect = range.getBoundingClientRect();
        // Do not discard normal content below the fold or horizontally scrollable content.
        if (rect.right <= 0 || rect.bottom <= 0) reason = 'Rendered text entirely left of or above document origin';
        if (rect.width === 0 || rect.height === 0) reason = reason || 'No rendered text area';
        const foreground = rgba(style.color);
        let background = [255,255,255,1];
        for (let ancestor = el; ancestor; ancestor = ancestor.parentElement) {
            const color = rgba(getComputedStyle(ancestor).backgroundColor);
            if (color.length >= 3 && (color.length < 4 || color[3] >= .99)) { background = color; break; }
        }
        if (foreground.length >= 3 && foreground.slice(0,3).every((c,i) => Math.abs(c-background[i]) < 3)) reason = 'Rendered text matches background';
        if (foreground.length === 4 && foreground[3] <= .01) reason = 'Rendered transparent text color';
        if (!reason && painted) {
            if (!emitted.has(paintedElement)) { if(painted.text) kept.push(painted.text); emitted.add(paintedElement); }
            excluded.push({reason:'DOM text covered by opaque generated text', text:text.slice(0,500), replacement:painted.text, pseudo:painted.pseudo});
        }
        else if (reason) excluded.push({reason, text:text.slice(0,500), bounds:{left:rect.left,right:rect.right,top:rect.top,bottom:rect.bottom}});
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
