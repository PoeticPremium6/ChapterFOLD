from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PageOrnamentPreset:
    key: str
    label: str
    description: str
    css_class: str
    css: str


NONE = PageOrnamentPreset(
    key="none",
    label="None",
    description="No decorative page ornament.",
    css_class="ornament-none",
    css="",
)


CLASSIC_RULE = PageOrnamentPreset(
    key="classic-rule",
    label="Classic Rule",
    description="Simple old-book horizontal rule around the page number.",
    css_class="ornament-classic-rule",
    css="""
.page-number-ornament.ornament-classic-rule::before,
.page-number-ornament.ornament-classic-rule::after {
  content: "";
  display: inline-block;
  width: 2.5em;
  border-top: 0.06em solid currentColor;
  margin: 0 0.55em 0.25em;
  opacity: 0.65;
}
""".strip(),
)


BOTANICAL_LEAF = PageOrnamentPreset(
    key="botanical-leaf",
    label="Botanical Leaf",
    description="Soft leaf ornaments around the page number.",
    css_class="ornament-botanical-leaf",
    css="""
.page-number-ornament.ornament-botanical-leaf::before {
  content: "❦";
  margin-right: 0.55em;
  font-size: 0.95em;
  opacity: 0.8;
}

.page-number-ornament.ornament-botanical-leaf::after {
  content: "❦";
  margin-left: 0.55em;
  font-size: 0.95em;
  opacity: 0.8;
}
""".strip(),
)


FLORAL_CORNER = PageOrnamentPreset(
    key="floral-corner",
    label="Floral Corner",
    description="Decorative floral corner-style marks near page numbers.",
    css_class="ornament-floral-corner",
    css="""
.page-number-ornament.ornament-floral-corner::before {
  content: "❧";
  margin-right: 0.6em;
  font-size: 1.05em;
  opacity: 0.85;
}

.page-number-ornament.ornament-floral-corner::after {
  content: "☙";
  margin-left: 0.6em;
  font-size: 1.05em;
  opacity: 0.85;
}
""".strip(),
)


GOTHIC_FLOURISH = PageOrnamentPreset(
    key="gothic-flourish",
    label="Gothic Flourish",
    description="A darker ornamental divider suited to classic, gothic, or dramatic books.",
    css_class="ornament-gothic-flourish",
    css="""
.page-number-ornament.ornament-gothic-flourish::before {
  content: "✦";
  margin-right: 0.65em;
  font-size: 0.85em;
  opacity: 0.85;
}

.page-number-ornament.ornament-gothic-flourish::after {
  content: "✦";
  margin-left: 0.65em;
  font-size: 0.85em;
  opacity: 0.85;
}
""".strip(),
)


STORYBOOK = PageOrnamentPreset(
    key="storybook",
    label="Storybook",
    description="Light whimsical ornaments for children’s books, poems, and fairy tales.",
    css_class="ornament-storybook",
    css="""
.page-number-ornament.ornament-storybook::before {
  content: "✧";
  margin-right: 0.55em;
  font-size: 0.9em;
  opacity: 0.75;
}

.page-number-ornament.ornament-storybook::after {
  content: "✧";
  margin-left: 0.55em;
  font-size: 0.9em;
  opacity: 0.75;
}
""".strip(),
)




VINE = PageOrnamentPreset(
    key="vine",
    label="Vine",
    description="A winding vine-like ornament for natural or romantic books.",
    css_class="ornament-vine",
    css="",
)


LAUREL = PageOrnamentPreset(
    key="laurel",
    label="Laurel",
    description="Classical laurel-style ornaments for formal books.",
    css_class="ornament-laurel",
    css="",
)


VICTORIAN_DOTS = PageOrnamentPreset(
    key="victorian-dots",
    label="Victorian Dots",
    description="A dotted Victorian-style page number ornament.",
    css_class="ornament-victorian-dots",
    css="",
)


CELESTIAL = PageOrnamentPreset(
    key="celestial",
    label="Celestial",
    description="Moon-and-star inspired ornaments for fantasy, poetry, and storybooks.",
    css_class="ornament-celestial",
    css="",
)


ROSE = PageOrnamentPreset(
    key="rose",
    label="Rose",
    description="Romantic floral ornaments with a rose-like feel.",
    css_class="ornament-rose",
    css="",
)


IVY = PageOrnamentPreset(
    key="ivy",
    label="Ivy",
    description="Ivy-leaf ornaments for botanical, gothic, or classic books.",
    css_class="ornament-ivy",
    css="",
)


ACANTHUS = PageOrnamentPreset(
    key="acanthus",
    label="Acanthus",
    description="Classical ornamental foliage inspired by old decorative borders.",
    css_class="ornament-acanthus",
    css="",
)


MINIMAL_DIVIDER = PageOrnamentPreset(
    key="minimal-divider",
    label="Minimal Divider",
    description="A clean understated divider for modern interiors.",
    css_class="ornament-minimal-divider",
    css="",
)




POETIC_VINE = PageOrnamentPreset(
    key="poetic-vine",
    label="Poetic Vine",
    description="A ChapterFOLD signature vine flourish with asymmetric botanical motion.",
    css_class="ornament-poetic-vine",
    css="",
)


MOON_GARDEN = PageOrnamentPreset(
    key="moon-garden",
    label="Moon Garden",
    description="A moonlit ornamental motif for poetry, fantasy, and fairytale interiors.",
    css_class="ornament-moon-garden",
    css="",
)


ROSE_WINDOW = PageOrnamentPreset(
    key="rose-window",
    label="Rose Window",
    description="A floral geometric motif inspired by decorative book windows and old bindings.",
    css_class="ornament-rose-window",
    css="",
)


IVY_THORN = PageOrnamentPreset(
    key="ivy-thorn",
    label="Ivy Thorn",
    description="A sharper botanical flourish for gothic, romantic, or classic books.",
    css_class="ornament-ivy-thorn",
    css="",
)


ASTERISM = PageOrnamentPreset(
    key="asterism",
    label="Asterism",
    description="A literary star-mark motif for elegant, minimal interiors.",
    css_class="ornament-asterism",
    css="",
)


BOOKBINDER_RULE = PageOrnamentPreset(
    key="bookbinder-rule",
    label="Bookbinder’s Rule",
    description="A ruled binder-style ornament combining linework and floral marks.",
    css_class="ornament-bookbinder-rule",
    css="",
)


PRESETS: tuple[PageOrnamentPreset, ...] = (
    NONE,
    CLASSIC_RULE,
    BOTANICAL_LEAF,
    FLORAL_CORNER,
    GOTHIC_FLOURISH,
    STORYBOOK,
    MINIMAL_DIVIDER,
    BOOKBINDER_RULE,
    ASTERISM,
    IVY_THORN,
    ROSE_WINDOW,
    MOON_GARDEN,
    POETIC_VINE,
    ACANTHUS,
    IVY,
    ROSE,
    CELESTIAL,
    VICTORIAN_DOTS,
    LAUREL,
    VINE,
)


def page_ornament_choices() -> list[tuple[str, str, str]]:
    return [(preset.key, preset.label, preset.description) for preset in PRESETS]


def get_page_ornament_preset(key: str | None) -> PageOrnamentPreset:
    normalized = (key or "none").strip().lower()
    for preset in PRESETS:
        if preset.key == normalized:
            return preset
    return NONE


def build_page_ornament_css(key: str | None) -> str:
    preset = get_page_ornament_preset(key)
    if preset.key == "none":
        return ""

    return f"""
/* ChapterFOLD page ornament: {preset.label} */
.page-number-ornament {{
  white-space: nowrap;
  letter-spacing: 0.02em;
}}

{preset.css}
""".strip() + "\n"


def wrap_page_number_content(page_number_expression: str, ornament_key: str | None) -> str:
    """Return CSS content() expression for ornamented page-number margin boxes.

    Example:
        counter(page)

    becomes:
        element(chapterfold-page-number)

    This helper intentionally returns a named string marker rather than raw HTML,
    because WeasyPrint page margin boxes support text content more reliably than
    arbitrary nested HTML in @page rules.
    """

    preset = get_page_ornament_preset(ornament_key)
    if preset.key == "none":
        return page_number_expression

    # Kept simple for Phase 1. Integration can use the CSS class when page
    # numbers are emitted as HTML spans; page margin boxes can still use normal
    # counter(page) until we wire the renderer-specific path.
    return page_number_expression


def ornamented_page_number_span(page_number: str, ornament_key: str | None) -> str:
    preset = get_page_ornament_preset(ornament_key)
    if preset.key == "none":
        return str(page_number)

    return f'<span class="page-number-ornament {preset.css_class}">{page_number}</span>'



VALID_PAGE_ORNAMENT_AMOUNTS = {"subtle", "balanced", "ornate"}
DEFAULT_PAGE_ORNAMENT_AMOUNT = "subtle"


def page_ornament_counter_content(
    counter_expression: str,
    ornament_key: str | None,
    ornament_amount: str | None = DEFAULT_PAGE_ORNAMENT_AMOUNT,
) -> str:
    """Return a CSS margin-box content expression with decorative ornaments."""

    preset = get_page_ornament_preset(ornament_key)
    amount = normalize_page_ornament_amount(ornament_amount)
    counter_expression = (counter_expression or "counter(page)").strip()

    if preset.key == "none":
        return counter_expression

    repeat = {"subtle": 1, "balanced": 2, "ornate": 3}[amount]

    motifs = {
        "classic-rule": (["—"], ["—"]),
        "botanical-leaf": (["❦"], ["❦"]),
        "floral-corner": (["❧"], ["☙"]),
        "gothic-flourish": (["✦"], ["✦"]),
        "storybook": (["✧"], ["✧"]),
        "vine": (["❧"], ["❦"]),
        "laurel": (["❬"], ["❭"]),
        "victorian-dots": (["•"], ["•"]),
        "celestial": (["☾"], ["✦"]),
        "rose": (["✿"], ["✿"]),
        "ivy": (["❦"], ["❧"]),
        "acanthus": (["❈"], ["❈"]),
        "minimal-divider": (["–"], ["–"]),

        # ChapterFOLD signature motifs.
        "poetic-vine": (["❧", "❦"], ["❦", "☙"]),
        "moon-garden": (["☾", "✦"], ["✦", "☽"]),
        "rose-window": (["✿", "❈"], ["❈", "✿"]),
        "ivy-thorn": (["❦", "✧"], ["✧", "❧"]),
        "asterism": (["⁂", "✦"], ["✦", "⁂"]),
        "bookbinder-rule": (["─", "❧"], ["☙", "─"]),
    }

    left_parts, right_parts = motifs.get(preset.key, ([], []))
    if not left_parts or not right_parts:
        return counter_expression

    left_text = " ".join(left_parts * repeat)
    right_text = " ".join(right_parts * repeat)

    return f'"{left_text} " {counter_expression} " {right_text}"'


def normalize_page_ornament_amount(value: str | None) -> str:
    amount = (value or DEFAULT_PAGE_ORNAMENT_AMOUNT).strip().lower()
    if amount not in VALID_PAGE_ORNAMENT_AMOUNTS:
        raise ValueError(
            f"Unknown page ornament amount: {value!r}. "
            f"Expected one of: {', '.join(sorted(VALID_PAGE_ORNAMENT_AMOUNTS))}"
        )
    return amount


def page_ornament_amount_choices() -> list[tuple[str, str, str]]:
    return [
        ("subtle", "Subtle", "One ornament on each side of the page number."),
        ("balanced", "Balanced", "Two ornaments on each side of the page number."),
        ("ornate", "Ornate", "Three ornaments on each side of the page number."),
    ]


SIGNATURE_ORNAMENT_KEYS = {
    "poetic-vine",
    "moon-garden",
    "rose-window",
    "ivy-thorn",
    "asterism",
    "bookbinder-rule",
}


def ordered_page_ornament_choices() -> list[tuple[str, str, str]]:
    """Return ornament choices with signature motifs promoted near the top."""

    choices = page_ornament_choices()
    none = [item for item in choices if item[0] == "none"]
    signature = [
        (key, f"Signature — {label}", description)
        for key, label, description in choices
        if key in SIGNATURE_ORNAMENT_KEYS
    ]
    basic = [
        item
        for item in choices
        if item[0] != "none" and item[0] not in SIGNATURE_ORNAMENT_KEYS
    ]
    return none + signature + basic


VALID_CHAPTER_ORNAMENTS = {
    "none",
    "classic-rule",
    "botanical-divider",
    "poetic-vine",
    "moon-garden",
    "rose-window",
    "bookbinder-rule",
}

DEFAULT_CHAPTER_ORNAMENT = "none"


def normalize_chapter_ornament(value: str | None) -> str:
    ornament = (value or DEFAULT_CHAPTER_ORNAMENT).strip().lower()
    if ornament not in VALID_CHAPTER_ORNAMENTS:
        raise ValueError(
            f"Unknown chapter ornament: {value!r}. "
            f"Expected one of: {', '.join(sorted(VALID_CHAPTER_ORNAMENTS))}"
        )
    return ornament


def chapter_ornament_choices() -> list[tuple[str, str, str]]:
    return [
        ("none", "None", "No chapter-start ornament."),
        ("classic-rule", "Classic Rule", "Simple traditional divider below chapter headings."),
        ("botanical-divider", "Botanical Divider", "Soft botanical flourish below chapter headings."),
        ("poetic-vine", "Signature — Poetic Vine", "ChapterFOLD vine flourish for chapter openings."),
        ("moon-garden", "Signature — Moon Garden", "Moonlit chapter-opening ornament."),
        ("rose-window", "Signature — Rose Window", "Floral geometric chapter-opening ornament."),
        ("bookbinder-rule", "Signature — Bookbinder’s Rule", "Ruled binder-style chapter-opening ornament."),
    ]


def chapter_ornament_text(value: str | None) -> str:
    ornament = normalize_chapter_ornament(value)
    mapping = {
        "none": "",
        "classic-rule": "—",
        "botanical-divider": "❦",
        "poetic-vine": "❧ ❦ ❧",
        "moon-garden": "☾ ✦ ☽",
        "rose-window": "✿ ❈ ✿",
        "bookbinder-rule": "─ ❧ ☙ ─",
    }
    return mapping.get(ornament, "")


def build_chapter_ornament_css(value: str | None) -> str:
    ornament = normalize_chapter_ornament(value)
    ornament_text = chapter_ornament_text(ornament)

    if ornament == "none" or not ornament_text:
        return ""

    return f"""
/* ChapterFOLD chapter-start ornament: {ornament} */
.chapter > h1:first-child::after,
.chapter > h2:first-child::after,
.first-body-chapter > h1:first-child::after,
.first-body-chapter > h2:first-child::after {{
  content: "{ornament_text}";
  display: block;
  margin: 0.65em auto 1.1em auto;
  text-align: center;
  font-size: 0.85em;
  font-weight: normal;
  letter-spacing: 0.18em;
  opacity: 0.82;
}}
""".strip() + "\n"
