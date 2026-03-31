"""ReadMe panel — Markdown via Python-Markdown, layout with CustomTkinter (crisp; no Tkhtml)."""

from __future__ import annotations

from pathlib import Path

import customtkinter as ctk

from core.constants import (
    CLI_REFERENCE_PATH,
    ENVIRONMENT_PATH,
    UPLOADER_DIR,
    README_PATH,
)

from gui.theme import COLORS, HEADING_COLORS, RADIUS, PAD
from gui.widgets import card, section_label

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


def _inline_plain(el) -> str:
    """Flatten inline tags to readable plain text (links show URL)."""
    from bs4 import NavigableString

    parts: list[str] = []

    def walk(node) -> None:
        if isinstance(node, NavigableString):
            parts.append(str(node))
            return
        if node.name == "a":
            href = (node.get("href") or "").strip()
            label = node.get_text()
            parts.append(f"{label} ({href})" if href else label)
            return
        if node.name == "code":
            parts.append(node.get_text())
            return
        if node.name in ("strong", "b", "em", "span"):
            parts.append(node.get_text())
            return
        if node.name == "br":
            parts.append("\n")
            return
        for ch in node.children:
            walk(ch)  # type: ignore[arg-type]

    for ch in el.children:
        walk(ch)
    return "".join(parts).strip()


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


class ReadMePanel(ctk.CTkFrame):
    """Tabbed docs: segmented control + stacked body frames (``lift``), not CTkTabview — avoids slow remap."""

    _DOC_TABS: tuple[tuple[str, Path], ...] = (
        ("README", README_PATH),
        ("CLI", CLI_REFERENCE_PATH),
        ("Environment", ENVIRONMENT_PATH),
    )

    def __init__(self, parent: ctk.CTkFrame, fonts: dict):
        # Match main window / Config tab (COLORS["bg"]), not card_bg.
        super().__init__(parent, fg_color=COLORS["bg"])
        self._mounted_doc_tabs: set[str] = set()
        self._tab_frames: dict[str, ctk.CTkFrame] = {}
        self.grid_columnconfigure(0, weight=1)
        self._doc_paths: dict[str, Path] = {}
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self._fonts = fonts
        self._build()

    def _on_doc_segment(self, name: str) -> None:
        """Show stacked tab body (``lift`` only — avoids CTkTabview ``grid_forget`` remap cost)."""
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
        self._seg = ctk.CTkSegmentedButton(
            self,
            values=titles,
            command=self._on_doc_segment,
            font=self._fonts["body_sm"],
            height=26,
            corner_radius=6,
            selected_color=COLORS["accent"],
            selected_hover_color=COLORS["accent_hover"],
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
                f"  pip install -r {UPLOADER_DIR / 'requirements.txt'}"
            )
            for title, _ in self._DOC_TABS:
                self._show_error_in_tab(self._tab_frames[title], msg)
            return

        self._doc_paths = {title: path for title, path in self._DOC_TABS}
        self._mounted_doc_tabs.clear()
        self._mount_doc_tab(self._tab_frames[first_title], first_path, first_title)
        self._mounted_doc_tabs.add(first_title)

    def _tab_scroll(self, parent: ctk.CTkFrame) -> ctk.CTkScrollableFrame:
        """Create a tab-level scrollable frame (same pattern as Config tab)."""
        scroll = ctk.CTkScrollableFrame(
            parent, fg_color="transparent",
            scrollbar_button_color=COLORS["card_border"],
            scrollbar_button_hover_color=COLORS["hover"],
        )
        scroll.grid(row=0, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)
        return scroll

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

    def _render_tag(self, scroll: ctk.CTkFrame, el, row: int) -> int:
        from bs4 import Tag

        name = el.name
        if name in ("h1", "h2", "h3", "h4"):
            return self._heading(scroll, el, row)
        if name == "p":
            return self._paragraph(scroll, el, row)
        if name == "pre":
            return self._pre(scroll, el, row)
        if name == "table":
            return self._table(scroll, el, row)
        if name in ("ul", "ol"):
            return self._list_block(scroll, el, row, ordered=(name == "ol"))
        if name == "blockquote":
            return self._blockquote(scroll, el, row)
        if name == "hr":
            sep = ctk.CTkFrame(scroll, height=1, fg_color=COLORS["card_border"])
            sep.grid(row=row, column=0, sticky="ew", padx=PAD["lg"], pady=10)
            return row + 1
        if name == "div":
            for ch in el.children:
                if isinstance(ch, Tag):
                    row = self._render_tag(scroll, ch, row)
            return row
        t = el.get_text("\n", strip=True)
        if t:
            self._body_label(scroll, row, t)
            return row + 1
        return row

    def _heading(self, scroll: ctk.CTkFrame, el: Tag, row: int) -> int:
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
            scroll, text=text, font=font, text_color=color,
            anchor="w", justify="left", wraplength=_WRAP,
        ).grid(row=row, column=0, sticky="ew", padx=PAD["lg"], pady=pad)
        row += 1
        if level == 1:
            line = ctk.CTkFrame(scroll, height=1, fg_color=COLORS["card_border"])
            line.grid(row=row, column=0, sticky="ew", padx=PAD["lg"], pady=(0, 8))
            row += 1
        return row

    def _paragraph(self, scroll: ctk.CTkFrame, el: Tag, row: int) -> int:
        text = _inline_plain(el)
        if not text:
            return row
        self._body_label(scroll, row, text)
        return row + 1

    def _body_label(self, scroll: ctk.CTkFrame, row: int, text: str) -> None:
        ctk.CTkLabel(
            scroll,
            text=text,
            font=self._fonts["body"],
            text_color=COLORS["text"],
            anchor="nw",
            justify="left",
            wraplength=_WRAP,
        ).grid(row=row, column=0, sticky="ew", padx=PAD["lg"], pady=(2, 6))

    def _pre(self, scroll: ctk.CTkFrame, el: Tag, row: int) -> int:
        code_el = el.find("code")
        raw = code_el.get_text() if code_el else el.get_text()
        box = ctk.CTkFrame(
            scroll, fg_color=COLORS["code_bg"], corner_radius=RADIUS["input"],
            border_width=1, border_color=COLORS["code_border"],
        )
        box.grid(row=row, column=0, sticky="ew", padx=PAD["lg"], pady=(4, 8))
        box.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            box,
            text=raw.rstrip("\n"),
            font=self._fonts["mono"],
            text_color=COLORS["cmd"],
            anchor="nw",
            justify="left",
            wraplength=_WRAP - 40,
        ).grid(row=0, column=0, sticky="ew", padx=12, pady=10)
        return row + 1

    def _table(self, scroll: ctk.CTkFrame, el: Tag, row: int) -> int:
        tbl = ctk.CTkFrame(
            scroll, fg_color=COLORS["code_bg"], corner_radius=RADIUS["input"],
            border_width=1, border_color=COLORS["code_border"],
        )
        tbl.grid(row=row, column=0, sticky="ew", padx=PAD["lg"], pady=(4, 10))
        r = 0
        for tr in el.find_all("tr"):
            cells = tr.find_all(["th", "td"])
            if not cells:
                continue
            n = len(cells)
            for c in range(n):
                tbl.grid_columnconfigure(c, weight=1, uniform="readme_tbl")
            is_head = cells[0].name == "th"
            for c, cell in enumerate(cells):
                txt = cell.get_text(strip=True)
                font = self._fonts["readme_h3"] if is_head else self._fonts["body"]
                tc = COLORS["accent"] if is_head else COLORS["text"]
                # anchor=nw + justify=left: CTkLabel otherwise centers wrapped lines in wide cells
                ctk.CTkLabel(
                    tbl,
                    text=txt,
                    font=font,
                    text_color=tc,
                    anchor="nw",
                    justify="left",
                    wraplength=360,
                ).grid(row=r, column=c, sticky="nsew", padx=10, pady=8)
            r += 1
        return row + 1

    def _list_block(self, scroll: ctk.CTkFrame, el: Tag, row: int, *, ordered: bool) -> int:
        idx = 1
        for li in el.find_all("li", recursive=False):
            bullet = f"{idx}. " if ordered else "•  "
            if ordered:
                idx += 1
            main = _li_main_text(li)
            ctk.CTkLabel(
                scroll,
                text=f"{bullet}{main}",
                font=self._fonts["body"],
                text_color=COLORS["text"],
                anchor="nw",
                justify="left",
                wraplength=_WRAP - 24,
            ).grid(row=row, column=0, sticky="ew", padx=(PAD["lg"] + 8, PAD["lg"]), pady=1)
            row += 1
            for nested in li.find_all(["ul", "ol"], recursive=False):
                row = self._list_block(scroll, nested, row, ordered=(nested.name == "ol"))
        return row

    def _blockquote(self, scroll: ctk.CTkScrollableFrame, el, row: int) -> int:
        from bs4 import Tag

        wrap = ctk.CTkFrame(
            scroll,
            fg_color=COLORS["code_bg"],
            corner_radius=RADIUS["input"],
            border_width=1,
            border_color=COLORS["accent"],
        )
        wrap.grid(row=row, column=0, sticky="ew", padx=PAD["lg"], pady=6)
        wrap.grid_columnconfigure(0, weight=1)
        sub = 0
        for ch in el.children:
            if isinstance(ch, Tag) and ch.name == "p":
                t = _inline_plain(ch)
                if t:
                    ctk.CTkLabel(
                        wrap, text=t, font=self._fonts["body"],
                        text_color=COLORS["text"], anchor="nw", justify="left",
                        wraplength=_WRAP - 48,
                    ).grid(row=sub, column=0, sticky="ew", padx=14, pady=6)
                    sub += 1
            elif isinstance(ch, Tag) and ch.name not in ("ul", "ol"):
                t = ch.get_text(strip=True)
                if t:
                    ctk.CTkLabel(
                        wrap, text=t, font=self._fonts["body"],
                        text_color=COLORS["text"], anchor="nw", justify="left",
                        wraplength=_WRAP - 48,
                    ).grid(row=sub, column=0, sticky="ew", padx=14, pady=6)
                    sub += 1
        return row + 1


def _li_main_text(li) -> str:
    """Text in <li> excluding nested lists."""
    from bs4 import Tag

    parts: list[str] = []
    for ch in li.children:
        if isinstance(ch, Tag) and ch.name in ("ul", "ol"):
            continue
        if isinstance(ch, Tag):
            parts.append(_inline_plain(ch) if ch.name == "p" else ch.get_text())
        else:
            s = str(ch).strip()
            if s:
                parts.append(s)
    return " ".join(parts).strip()
