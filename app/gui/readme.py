"""ReadMe panel — Markdown via Python-Markdown, layout with CustomTkinter.

Supports rich inline styling: bold, italic, inline code, and clickable links.
"""

from __future__ import annotations

import webbrowser
from dataclasses import dataclass
from pathlib import Path

import customtkinter as ctk

from core.constants import (
    CLI_REFERENCE_PATH,
    ENVIRONMENT_PATH,
    BUNDLE_DIR,
    README_PATH,
)

from gui.theme import COLORS, HEADING_COLORS, RADIUS, PAD
from gui.widgets import card, scrollable_frame, section_label, segmented_button

_MD_EXTENSIONS = (
    "markdown.extensions.fenced_code",
    "markdown.extensions.sane_lists",
    "markdown.extensions.tables",
    "markdown.extensions.nl2br",
)

_WRAP = 820


def _markdown_to_html_fragment(md: str) -> str:
    import markdown

    return markdown.markdown(md, extensions=list(_MD_EXTENSIONS))


# ── Inline span model ─────────────────────────────────────────────────────────

@dataclass(slots=True)
class _Span:
    text: str
    bold: bool = False
    italic: bool = False
    code: bool = False
    href: str | None = None


_BLOCK_TAGS = frozenset({"ul", "ol", "table", "pre", "blockquote", "div", "hr",
                         "h1", "h2", "h3", "h4", "h5", "h6"})


def _collect_spans(node, *, bold: bool = False, italic: bool = False) -> list[_Span]:
    """Recursively walk inline HTML nodes and produce a flat list of styled spans."""
    from bs4 import NavigableString, Tag

    spans: list[_Span] = []
    for child in node.children:
        if isinstance(child, NavigableString):
            text = str(child)
            if text:
                spans.append(_Span(text=text, bold=bold, italic=italic))
        elif isinstance(child, Tag):
            if child.name in _BLOCK_TAGS:
                continue
            if child.name == "br":
                spans.append(_Span(text="\n"))
            elif child.name in ("strong", "b"):
                spans.extend(_collect_spans(child, bold=True, italic=italic))
            elif child.name in ("em", "i"):
                spans.extend(_collect_spans(child, bold=bold, italic=True))
            elif child.name == "code":
                spans.append(_Span(text=child.get_text(), code=True))
            elif child.name == "a":
                href = (child.get("href") or "").strip()
                spans.append(_Span(text=child.get_text(), href=href or None, bold=bold, italic=italic))
            else:
                spans.extend(_collect_spans(child, bold=bold, italic=italic))
    return spans


def _coalesce_spans(spans: list[_Span]) -> list[_Span]:
    """Merge adjacent spans with identical styling to reduce widget count."""
    if not spans:
        return []
    merged: list[_Span] = [_Span(text=spans[0].text, bold=spans[0].bold, italic=spans[0].italic,
                                   code=spans[0].code, href=spans[0].href)]
    for s in spans[1:]:
        prev = merged[-1]
        if (s.bold == prev.bold and s.italic == prev.italic
                and s.code == prev.code and s.href == prev.href):
            prev.text += s.text
        else:
            merged.append(_Span(text=s.text, bold=s.bold, italic=s.italic,
                                 code=s.code, href=s.href))
    return merged


def _spans_plain(spans: list[_Span]) -> str:
    """Fallback: flatten spans back to plain text."""
    return "".join(s.text for s in spans).strip()


# ── Import check ──────────────────────────────────────────────────────────────

def _renderer_import_error() -> str | None:
    try:
        import markdown  # noqa: F401
    except ImportError as e:
        return str(e)
    try:
        from bs4 import BeautifulSoup as _BS4  # noqa: F401
    except ImportError as e:
        return str(e)
    return None


# ── Panel ─────────────────────────────────────────────────────────────────────

class ReadMePanel(ctk.CTkFrame):
    """Tabbed docs: segmented control + stacked body frames (``lift``)."""

    _DOC_TABS: tuple[tuple[str, Path], ...] = (
        ("README", README_PATH),
        ("CLI", CLI_REFERENCE_PATH),
        ("Environment", ENVIRONMENT_PATH),
    )

    def __init__(self, parent: ctk.CTkFrame, fonts: dict):
        super().__init__(parent, fg_color=COLORS["bg"])
        self._mounted_doc_tabs: set[str] = set()
        self._tab_frames: dict[str, ctk.CTkFrame] = {}
        self.grid_columnconfigure(0, weight=1)
        self._doc_paths: dict[str, Path] = {}
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self._fonts = fonts
        self._build()

    # ── Font resolver for inline spans ─────────────────────────────────────

    def _span_font(self, span: _Span) -> ctk.CTkFont:
        if span.code:
            return self._fonts["inline_code"]
        if span.bold and span.italic:
            return self._fonts["body_bold_italic"]
        if span.bold:
            return self._fonts["body_bold"]
        if span.italic:
            return self._fonts["body_italic"]
        return self._fonts["body"]

    @staticmethod
    def _span_color(span: _Span) -> str:
        if span.href:
            return COLORS["accent"]
        if span.code:
            return COLORS["cmd"]
        return COLORS["text"]

    # ── Inline renderer ────────────────────────────────────────────────────

    def _render_inline(
        self, parent: ctk.CTkFrame, element, row: int, *,
        padx: int | tuple[int, int] = 0,
        pady: tuple[int, int] = (2, 6),
        wraplength: int = _WRAP,
        prefix: str = "",
    ) -> int:
        """Render inline HTML nodes as styled labels in a flow container."""
        spans = _coalesce_spans(_collect_spans(element))
        if not spans and not prefix:
            return row

        has_rich = any(s.bold or s.italic or s.code or s.href for s in spans)

        if not has_rich and not prefix:
            text = _spans_plain(spans)
            if not text:
                return row
            ctk.CTkLabel(
                parent, text=text, font=self._fonts["body"],
                text_color=COLORS["text"], anchor="nw", justify="left",
                wraplength=wraplength,
            ).grid(row=row, column=0, sticky="ew", padx=padx, pady=pady)
            return row + 1

        if not has_rich and prefix:
            text = prefix + _spans_plain(spans)
            ctk.CTkLabel(
                parent, text=text, font=self._fonts["body"],
                text_color=COLORS["text"], anchor="nw", justify="left",
                wraplength=wraplength,
            ).grid(row=row, column=0, sticky="ew", padx=padx, pady=pady)
            return row + 1

        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.grid(row=row, column=0, sticky="ew", padx=padx, pady=pady)

        col = 0
        if prefix:
            ctk.CTkLabel(
                container, text=prefix, font=self._fonts["body"],
                text_color=COLORS["text"], anchor="w",
            ).grid(row=0, column=col, sticky="w")
            col += 1

        for span in spans:
            if not span.text:
                continue

            lines = span.text.split("\n")
            for li_idx, line in enumerate(lines):
                if li_idx > 0:
                    col = 0
                if not line:
                    continue

                font = self._span_font(span)
                color = self._span_color(span)

                lbl = ctk.CTkLabel(
                    container, text=line, font=font,
                    text_color=color, anchor="w",
                )

                if span.code:
                    lbl.configure(
                        fg_color=COLORS["code_bg"],
                        corner_radius=4,
                    )

                if span.href:
                    lbl.configure(cursor="hand2")
                    url = span.href
                    lbl.bind("<Button-1>", lambda _e, u=url: webbrowser.open(u))

                lbl.grid(row=0, column=col, sticky="w")
                col += 1

        return row + 1

    # ── Tab infrastructure ─────────────────────────────────────────────────

    def _on_doc_segment(self, name: str) -> None:
        fr = self._tab_frames.get(name)
        if fr is not None:
            fr.lift()
        if not name or name in self._mounted_doc_tabs:
            return
        path = self._doc_paths.get(name)
        if path is None or fr is None:
            return
        self._mount_doc_tab(fr, path, name)
        self._mounted_doc_tabs.add(name)

    def _build(self) -> None:
        titles = [t[0] for t in self._DOC_TABS]
        self._seg = segmented_button(
            self, values=titles,
            command=self._on_doc_segment,
            font=self._fonts["body_sm"],
        )
        self._seg.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        stack_host = ctk.CTkFrame(self, fg_color="transparent")
        stack_host.grid(row=1, column=0, sticky="nsew")
        stack_host.grid_columnconfigure(0, weight=1)
        stack_host.grid_rowconfigure(0, weight=1)

        self._tab_frames = {}
        for title, _path in self._DOC_TABS:
            fr = ctk.CTkFrame(stack_host, fg_color="transparent")
            fr.grid(row=0, column=0, sticky="nsew")
            fr.grid_columnconfigure(0, weight=1)
            fr.grid_rowconfigure(0, weight=1)
            self._tab_frames[title] = fr

        first_title, first_path = self._DOC_TABS[0]
        self._seg.set(first_title)
        self._tab_frames[first_title].lift()

        missing = _renderer_import_error()
        if missing:
            msg = (
                "Read Me dependencies missing.\n\n"
                f"{missing}\n\n"
                "Install with:\n"
                f"  pip install -r {BUNDLE_DIR / 'requirements.txt'}"
            )
            for title, _ in self._DOC_TABS:
                self._show_error_in_tab(self._tab_frames[title], msg)
            return

        self._doc_paths = {title: path for title, path in self._DOC_TABS}
        self._mounted_doc_tabs.clear()
        self._mount_doc_tab(self._tab_frames[first_title], first_path, first_title)
        self._mounted_doc_tabs.add(first_title)

    @staticmethod
    def _tab_scroll(parent: ctk.CTkFrame) -> ctk.CTkScrollableFrame:
        return scrollable_frame(parent, row=0, column=0, sticky="nsew")

    def _show_error_in_tab(self, parent: ctk.CTkFrame, message: str) -> None:
        scroll = self._tab_scroll(parent)
        c = card(scroll, row=0, column=0, sticky="ew", pady=(0, 12))
        c.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            c, text=message,
            font=self._fonts["body"],
            text_color=COLORS["error"],
            justify="left", anchor="nw", wraplength=720,
        ).grid(row=0, column=0, sticky="ew", padx=PAD["lg"], pady=PAD["lg"])

    def _mount_doc_tab(self, frame: ctk.CTkFrame, path: Path, tab_title: str) -> None:
        if not path.is_file():
            self._show_error_in_tab(frame, f"{path.name} not found.\nExpected:\n{path}")
            return
        try:
            md = path.read_text(encoding="utf-8")
        except OSError as exc:
            self._show_error_in_tab(frame, f"Could not read {path.name}:\n{exc}")
            return

        try:
            from bs4 import BeautifulSoup, Tag as BsTag, NavigableString as BsStr

            html = _markdown_to_html_fragment(md)
            soup = BeautifulSoup(f"<div id='md'>{html}</div>", "html.parser")
            root = soup.find("div", id="md")
            if root is None:
                raise RuntimeError("parse failed")

            scroll = self._tab_scroll(frame)
            doc_card = card(scroll, row=0, column=0, sticky="ew", pady=(0, 12))
            doc_card.grid_columnconfigure(0, weight=1)

            section_label(doc_card, tab_title, self._fonts["section"]).grid(
                row=0, column=0, sticky="w", padx=PAD["lg"], pady=(PAD["md"], 5),
            )

            row = 1
            for child in root.children:
                if isinstance(child, BsStr) and not str(child).strip():
                    continue
                if isinstance(child, BsTag):
                    row = self._render_tag(doc_card, child, row)
        except Exception as exc:
            self._show_error_in_tab(
                frame,
                f"Could not render {path.name}:\n{exc}\n\n"
                "Install: pip install markdown beautifulsoup4",
            )

    # ── Block-level renderers ──────────────────────────────────────────────

    def _render_tag(self, parent: ctk.CTkFrame, el, row: int) -> int:
        from bs4 import Tag

        name = el.name
        if name in ("h1", "h2", "h3", "h4"):
            return self._heading(parent, el, row)
        if name == "p":
            return self._paragraph(parent, el, row)
        if name == "pre":
            return self._pre(parent, el, row)
        if name == "table":
            return self._table(parent, el, row)
        if name in ("ul", "ol"):
            return self._list_block(parent, el, row, ordered=(name == "ol"))
        if name == "blockquote":
            return self._blockquote(parent, el, row)
        if name == "hr":
            ctk.CTkFrame(parent, height=1, fg_color=COLORS["card_border"]).grid(
                row=row, column=0, sticky="ew", padx=PAD["lg"], pady=10,
            )
            return row + 1
        if name == "div":
            for ch in el.children:
                if isinstance(ch, Tag):
                    row = self._render_tag(parent, ch, row)
            return row
        t = el.get_text("\n", strip=True)
        if t:
            ctk.CTkLabel(
                parent, text=t, font=self._fonts["body"],
                text_color=COLORS["text"], anchor="nw", justify="left",
                wraplength=_WRAP,
            ).grid(row=row, column=0, sticky="ew", padx=PAD["lg"], pady=(2, 6))
            return row + 1
        return row

    def _heading(self, parent: ctk.CTkFrame, el, row: int) -> int:
        level = int(el.name[1])
        if level == 1:
            font = self._fonts["readme_h1"]
            color = COLORS["accent"]
        elif level == 2:
            font = self._fonts["readme_h2"]
            color = HEADING_COLORS.get(2, COLORS["section"])
        else:
            font = self._fonts["readme_h3"]
            color = HEADING_COLORS.get(min(level, 3), COLORS["accent"])
        text = el.get_text(strip=True)
        pad = (PAD["md"], 4) if level == 1 else (12, 2)
        ctk.CTkLabel(
            parent, text=text, font=font, text_color=color,
            anchor="w", justify="left", wraplength=_WRAP,
        ).grid(row=row, column=0, sticky="ew", padx=PAD["lg"], pady=pad)
        row += 1
        if level == 1:
            ctk.CTkFrame(parent, height=1, fg_color=COLORS["card_border"]).grid(
                row=row, column=0, sticky="ew", padx=PAD["lg"], pady=(0, 8),
            )
            row += 1
        return row

    def _paragraph(self, parent: ctk.CTkFrame, el, row: int) -> int:
        return self._render_inline(parent, el, row, padx=PAD["lg"])

    def _pre(self, parent: ctk.CTkFrame, el, row: int) -> int:
        code_el = el.find("code")
        raw = code_el.get_text() if code_el else el.get_text()
        box = ctk.CTkFrame(
            parent, fg_color=COLORS["code_bg"], corner_radius=RADIUS["input"],
            border_width=1, border_color=COLORS["code_border"],
        )
        box.grid(row=row, column=0, sticky="ew", padx=PAD["lg"], pady=(4, 8))
        box.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            box, text=raw.rstrip("\n"), font=self._fonts["mono"],
            text_color=COLORS["cmd"], anchor="nw", justify="left",
            wraplength=_WRAP - 40,
        ).grid(row=0, column=0, sticky="ew", padx=12, pady=10)
        return row + 1

    def _table(self, parent: ctk.CTkFrame, el, row: int) -> int:
        tbl = ctk.CTkFrame(
            parent, fg_color=COLORS["code_bg"], corner_radius=RADIUS["input"],
            border_width=1, border_color=COLORS["code_border"],
        )
        tbl.grid(row=row, column=0, sticky="ew", padx=PAD["lg"], pady=(4, 10))
        r = 0
        for tr in el.find_all("tr"):
            cells = tr.find_all(["th", "td"])
            if not cells:
                continue
            for c in range(len(cells)):
                tbl.grid_columnconfigure(c, weight=1, uniform="readme_tbl")
            is_head = cells[0].name == "th"
            for c, cell in enumerate(cells):
                txt = cell.get_text(strip=True)
                font = self._fonts["readme_h3"] if is_head else self._fonts["body"]
                tc = COLORS["accent"] if is_head else COLORS["text"]
                ctk.CTkLabel(
                    tbl, text=txt, font=font, text_color=tc,
                    anchor="nw", justify="left", wraplength=360,
                ).grid(row=r, column=c, sticky="nsew", padx=10, pady=8)
            r += 1
        return row + 1

    def _list_block(self, parent: ctk.CTkFrame, el, row: int, *, ordered: bool) -> int:
        idx = 1
        for li in el.find_all("li", recursive=False):
            bullet = f"{idx}. " if ordered else "•  "
            if ordered:
                idx += 1
            li_padx = (PAD["lg"] + 8, PAD["lg"])
            row = self._render_inline(
                parent, li, row,
                padx=li_padx, pady=(1, 1),
                wraplength=_WRAP - 24,
                prefix=bullet,
            )
            for nested in li.find_all(["ul", "ol"], recursive=False):
                row = self._list_block(parent, nested, row, ordered=(nested.name == "ol"))
        return row

    def _blockquote(self, parent: ctk.CTkFrame, el, row: int) -> int:
        from bs4 import Tag

        wrap = ctk.CTkFrame(
            parent, fg_color=COLORS["code_bg"],
            corner_radius=RADIUS["input"],
            border_width=1, border_color=COLORS["accent"],
        )
        wrap.grid(row=row, column=0, sticky="ew", padx=PAD["lg"], pady=6)
        wrap.grid_columnconfigure(0, weight=1)
        sub = 0
        for ch in el.children:
            if not isinstance(ch, Tag) or ch.name in ("ul", "ol"):
                continue
            sub = self._render_inline(
                wrap, ch, sub,
                padx=14, pady=(6, 6),
                wraplength=_WRAP - 48,
            )
        return row + 1
