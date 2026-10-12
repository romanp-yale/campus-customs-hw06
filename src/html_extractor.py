"""Local extractor copied from app/website_to_text.py via html-reader skill; no sanitizer."""
import re
from html.parser import HTMLParser

DROP_TAGS = {
    "script", "style", "noscript", "template", "svg", "canvas", "iframe", "object", "embed",
    # Usually chrome rather than the page's human-readable content.
    "nav", "aside", "footer",
}

CONTENT_TAGS = {"article", "main", "section", "p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "blockquote", "pre"}

BLOCK_TAGS = CONTENT_TAGS | {"div", "br", "tr", "header", "footer", "nav", "aside", "table"}

class TextExtractor(HTMLParser):
    """Small, dependency-free HTML-to-text parser."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.tag_stack: list[str] = []
        self.drop_depth = 0
        self.content_score = 0
        self.candidates: list[tuple[int, int, int]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        self.tag_stack.append(tag)
        if tag in DROP_TAGS:
            self.drop_depth += 1
        if tag in BLOCK_TAGS and self.drop_depth == 0:
            self.parts.append("\n")
        if tag in CONTENT_TAGS and self.drop_depth == 0:
            self.content_score += 1

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in DROP_TAGS and self.drop_depth:
            self.drop_depth -= 1
        if tag in BLOCK_TAGS and self.drop_depth == 0:
            self.parts.append("\n")
        for index in range(len(self.tag_stack) - 1, -1, -1):
            if self.tag_stack[index] == tag:
                del self.tag_stack[index:]
                break

    def handle_data(self, data: str) -> None:
        if self.drop_depth == 0 and data.strip():
            self.parts.append(data)

    def text(self) -> str:
        raw = "".join(self.parts).replace("\xa0", " ")
        lines = [re.sub(r"[ \t\r\f\v]+", " ", line).strip() for line in raw.splitlines()]
        lines = [line for line in lines if line]
        # Remove repeated adjacent lines, a common artifact of navigation markup.
        result: list[str] = []
        for line in lines:
            if not result or line != result[-1]:
                result.append(line)
        return "\n\n".join(result)
