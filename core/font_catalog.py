from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FontChoice:
    key: str
    label: str
    css_stack: str
    sample: str
    description: str

    @property
    def dropdown_label(self) -> str:
        return f"{self.label} — {self.description}"


FONT_CHOICES: tuple[FontChoice, ...] = (
    FontChoice(
        "classic-serif",
        "Classic Serif",
        '"Garamond", "EB Garamond", "Cormorant Garamond", "DejaVu Serif", "Noto Serif", serif',
        "Classic Serif — Pride & Prejudice",
        "traditional English classics",
    ),
    FontChoice(
        "eb-garamond",
        "EB Garamond",
        '"EB Garamond", "Garamond", "Cormorant Garamond", "DejaVu Serif", serif',
        "EB Garamond — elegant public-domain prose",
        "classic novels and literary editions",
    ),
    FontChoice(
        "cormorant",
        "Cormorant",
        '"Cormorant Garamond", "EB Garamond", "Garamond", "DejaVu Serif", serif',
        "Cormorant — refined old-book elegance",
        "ornate literary styling",
    ),
    FontChoice(
        "libre-baskerville",
        "Libre Baskerville",
        '"Libre Baskerville", "Baskerville", "Georgia", "DejaVu Serif", serif',
        "Libre Baskerville — polished and readable",
        "premium-looking printed books",
    ),
    FontChoice(
        "crimson-pro",
        "Crimson Pro",
        '"Crimson Pro", "Crimson Text", "Garamond", "DejaVu Serif", serif',
        "Crimson Pro — scholarly classic",
        "essays, classics, academic prose",
    ),
    FontChoice(
        "vollkorn",
        "Vollkorn",
        '"Vollkorn", "Georgia", "DejaVu Serif", "Noto Serif", serif',
        "Vollkorn — sturdy book serif",
        "long-form readable fiction",
    ),
    FontChoice(
        "literata",
        "Literata",
        '"Literata", "Noto Serif", "DejaVu Serif", "Georgia", serif',
        "Literata — modern digital book",
        "ebooks and web-first editions",
    ),
    FontChoice(
        "source-serif",
        "Source Serif",
        '"Source Serif 4", "Source Serif Pro", "Noto Serif", "DejaVu Serif", serif',
        "Source Serif — clean publishing style",
        "modern open-access publishing",
    ),
    FontChoice(
        "gentium",
        "Gentium",
        '"Gentium Book Plus", "Gentium Plus", "Gentium", "Noto Serif", "DejaVu Serif", serif',
        "Gentium — multilingual scholarship",
        "historical and multilingual works",
    ),
    FontChoice(
        "alegreya",
        "Alegreya",
        '"Alegreya", "Georgia", "DejaVu Serif", "Noto Serif", serif',
        "Alegreya — lively literary rhythm",
        "characterful fiction",
    ),
    FontChoice(
        "bookman",
        "Bookman",
        '"Bookman Old Style", "URW Bookman", "Georgia", "DejaVu Serif", serif',
        "Bookman — warm and friendly",
        "children’s books and cosy fiction",
    ),
    FontChoice(
        "palatino",
        "Palatino",
        '"Palatino Linotype", "Palatino", "Book Antiqua", "URW Palladio L", "DejaVu Serif", serif',
        "Palatino — warm classical prose",
        "general-purpose literary books",
    ),
    FontChoice(
        "readable-serif",
        "Readable Serif",
        '"Liberation Serif", "DejaVu Serif", "Noto Serif", "Georgia", serif',
        "Readable Serif — clear body text",
        "safe system fallback",
    ),
    FontChoice(
        "large-print",
        "Large Print Serif",
        '"Georgia", "DejaVu Serif", "Noto Serif", serif',
        "Large Print Serif — accessible reading",
        "large-print editions",
    ),
    FontChoice(
        "atkinson",
        "Atkinson Hyperlegible",
        '"Atkinson Hyperlegible", "Verdana", "DejaVu Sans", "Noto Sans", sans-serif',
        "Atkinson Hyperlegible — accessible",
        "maximum readability",
    ),
    FontChoice(
        "open-sans",
        "Open Sans",
        '"Open Sans", "Noto Sans", "DejaVu Sans", "Arial", sans-serif',
        "Open Sans — clean modern sans",
        "manuals and contemporary books",
    ),
    FontChoice(
        "source-sans",
        "Source Sans",
        '"Source Sans 3", "Source Sans Pro", "Noto Sans", "DejaVu Sans", sans-serif',
        "Source Sans — professional clarity",
        "reports and open-access documents",
    ),
    FontChoice(
        "lora",
        "Lora",
        '"Lora", "Georgia", "DejaVu Serif", "Noto Serif", serif',
        "Lora — soft modern literary",
        "web-to-print literary editions",
    ),
    FontChoice(
        "bitter",
        "Bitter",
        '"Bitter", "Georgia", "DejaVu Serif", "Noto Serif", serif',
        "Bitter — slab serif readability",
        "quirky but readable editions",
    ),
    FontChoice(
        "merriweather",
        "Merriweather",
        '"Merriweather", "Georgia", "DejaVu Serif", "Noto Serif", serif',
        "Merriweather — screen-friendly serif",
        "digital reading comfort",
    ),
    FontChoice(
        "fell-english",
        "Fell English",
        '"IM FELL English", "IM FELL DW Pica", "Garamond", "EB Garamond", "DejaVu Serif", serif',
        "Fell English — antique letterpress",
        "older public-domain works",
    ),
    FontChoice(
        "typewriter",
        "Typewriter",
        '"Courier Prime", "Courier New", "Liberation Mono", "DejaVu Sans Mono", monospace',
        "Typewriter — archival manuscript",
        "letters, scripts, archival texts",
    ),
    FontChoice(
        "caveat",
        "Caveat",
        '"Caveat", "Segoe Print", "Comic Sans MS", "URW Chancery L", cursive',
        "Caveat — casual handwritten",
        "playful short editions",
    ),
    FontChoice(
        "dancing-script",
        "Dancing Script",
        '"Dancing Script", "Segoe Script", "URW Chancery L", cursive',
        "Dancing Script — lively cursive",
        "decorative titles or short books",
    ),
    FontChoice(
        "playwrite",
        "Playwrite",
        '"Playwrite GB S", "Playwrite US Trad", "Segoe Print", "URW Chancery L", cursive',
        "Playwrite — readable cursive",
        "handwritten-style special editions",
    ),
    FontChoice(
        "readable-cursive",
        "Readable Cursive",
        '"Segoe Print", "Comic Sans MS", "URW Chancery L", "DejaVu Serif", serif',
        "Readable Cursive — handwritten charm",
        "safe cursive fallback",
    ),
    FontChoice(
        "unicode-global",
        "Unicode Global",
        '"Noto Serif", "DejaVu Serif", "Noto Serif CJK SC", "Noto Sans CJK SC", "WenQuanYi Micro Hei", serif',
        "Unicode Global — ö ä å / 你好 / Καλημέρα",
        "mixed-language books",
    ),
    FontChoice(
        "cjk-serif",
        "CJK Serif",
        '"Noto Serif CJK SC", "Noto Serif CJK TC", "Noto Serif CJK JP", "Noto Serif", "DejaVu Serif", serif',
        "CJK Serif — 你好，世界",
        "Chinese/Japanese/Korean serif",
    ),
    FontChoice(
        "cjk-sans",
        "CJK Sans",
        '"Noto Sans CJK SC", "Noto Sans CJK TC", "Noto Sans CJK JP", "WenQuanYi Micro Hei", "DejaVu Sans", sans-serif',
        "CJK Sans — 你好，世界",
        "Chinese/Japanese/Korean sans",
    ),
)


def get_font_choice(key: str | None) -> FontChoice:
    wanted = (key or "").strip()
    for choice in FONT_CHOICES:
        if choice.key == wanted:
            return choice
    return FONT_CHOICES[0]


def font_css_stack(key: str | None) -> str:
    return get_font_choice(key).css_stack
