from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class SettingChoice:
    value: str
    label: str
    description: str = ""


@dataclass(frozen=True)
class SettingSpec:
    key: str
    label: str
    description: str
    default: Any
    choices: list[SettingChoice] = field(default_factory=list)
    web_visible: bool = True
    advanced: bool = False
    category: str = "general"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["choices"] = [asdict(choice) for choice in self.choices]
        return data


def _choices(items: list[tuple[str, str, str]]) -> list[SettingChoice]:
    return [SettingChoice(value=value, label=label, description=description) for value, label, description in items]


WEB_SAFE_SETTINGS: tuple[SettingSpec, ...] = (
    SettingSpec(
        key="variant",
        label="Cleanup mode",
        description="Controls how aggressively ChapterFOLD cleans and restructures the input.",
        default="standard",
        category="content",
        choices=_choices(
            [
                ("standard", "Standard", "Balanced cleanup for most books."),
                ("aggressive-cleanup", "Aggressive cleanup", "More forceful cleanup for messy sources."),
                ("paragraph-dialogue-merge", "Dialogue merge", "Experimental cleanup for dialogue-heavy texts."),
            ]
        ),
    ),
    SettingSpec(
        key="contents_mode",
        label="Contents page",
        description="Choose whether to keep, remove, or rebuild the table of contents.",
        default="rebuild",
        category="content",
        choices=_choices(
            [
                ("keep", "Keep", "Keep the source contents page when possible."),
                ("remove", "Remove", "Remove the source contents page."),
                ("rebuild", "Rebuild", "Generate a cleaner contents page."),
                ("rebuild-paged", "Rebuild with page numbers", "Generate a paged contents page when supported."),
            ]
        ),
    ),
    SettingSpec(
        key="page_number_start_mode",
        label="Page number start",
        description="Controls where visible page numbers begin.",
        default="after-title-page",
        category="layout",
        choices=_choices(
            [
                ("after-title-page", "After title page", "Hide the title page number and start after it."),
                ("main-text", "Main text", "Start page numbers at the first main-text chapter."),
                ("first-page", "First page", "Show page numbers from the first page."),
                ("none", "None", "Do not show page numbers."),
            ]
        ),
    ),
    SettingSpec(
        key="front_matter_page_number_style",
        label="Front matter numbers",
        description="Controls page numbering style before the main text.",
        default="hidden",
        category="layout",
        advanced=True,
        choices=_choices(
            [
                ("hidden", "Hidden", "Do not show front matter page numbers."),
                ("roman-lower", "Lowercase Roman", "Use i, ii, iii for front matter."),
                ("roman-upper", "Uppercase Roman", "Use I, II, III for front matter."),
                ("arabic", "Arabic", "Use normal numbers for front matter."),
            ]
        ),
    ),
    SettingSpec(
        key="page_ornament",
        label="Page number ornament",
        description="Decorative motif around visible page numbers.",
        default="none",
        category="ornaments",
        choices=_choices(
            [
                ("none", "None", "No page number ornament."),
                ("poetic-vine", "Signature — Poetic Vine", "A ChapterFOLD vine flourish."),
                ("moon-garden", "Signature — Moon Garden", "A moonlit ornamental motif."),
                ("rose-window", "Signature — Rose Window", "A floral geometric ornament."),
                ("ivy-thorn", "Signature — Ivy Thorn", "A sharper botanical flourish."),
                ("asterism", "Signature — Asterism", "A literary star-mark motif."),
                ("bookbinder-rule", "Signature — Bookbinder’s Rule", "Binder-style linework and floral marks."),
                ("classic-rule", "Classic Rule", "Simple rule ornament."),
                ("botanical-leaf", "Botanical Leaf", "Simple botanical mark."),
                ("floral-corner", "Floral Corner", "Classic floral corner marks."),
            ]
        ),
    ),
    SettingSpec(
        key="page_ornament_amount",
        label="Ornament amount",
        description="Controls how elaborate the page number ornament appears.",
        default="subtle",
        category="ornaments",
        choices=_choices(
            [
                ("subtle", "Subtle", "Small and quiet."),
                ("balanced", "Balanced", "A more visible decorative treatment."),
                ("ornate", "Ornate", "The most decorative option."),
            ]
        ),
    ),
    SettingSpec(
        key="chapter_ornament",
        label="Chapter ornament",
        description="Decorative flourish below chapter headings.",
        default="none",
        category="ornaments",
        choices=_choices(
            [
                ("none", "None", "No chapter-start ornament."),
                ("classic-rule", "Classic Rule", "Simple traditional divider."),
                ("botanical-divider", "Botanical Divider", "Soft botanical flourish."),
                ("poetic-vine", "Signature — Poetic Vine", "ChapterFOLD vine flourish."),
                ("moon-garden", "Signature — Moon Garden", "Moonlit chapter-opening ornament."),
                ("rose-window", "Signature — Rose Window", "Floral geometric ornament."),
                ("bookbinder-rule", "Signature — Bookbinder’s Rule", "Ruled binder-style ornament."),
            ]
        ),
    ),
    SettingSpec(
        key="paragraph_spacing_mode",
        label="Paragraph style",
        description="Controls paragraph spacing and indentation.",
        default="traditional",
        category="layout",
        choices=_choices(
            [
                ("traditional", "Traditional", "Indented paragraphs with book-like spacing."),
                ("uniform", "Uniform", "Consistent spacing between paragraphs."),
                ("no-indents", "No indents", "Block-style paragraphs."),
                ("indented-compact", "Compact indented", "Tighter indented paragraph style."),
            ]
        ),
    ),
    SettingSpec(
        key="page_size_preset",
        label="Page size",
        description="Select the output trim/page size.",
        default="default-trade",
        category="print",
        choices=_choices(
            [
                ("default-trade", "Default trade", "General-purpose book size."),
                ("a4", "A4", "Standard A4 page size."),
                ("a5", "A5", "Common small book/zine size."),
                ("a6", "A6", "Pocket-sized format."),
                ("letter", "Letter", "US Letter."),
                ("half-letter", "Half Letter", "Compact US format."),
                ("trade-5x8", "Trade 5×8", "Small trade paperback."),
                ("trade-6x9", "Trade 6×9", "Common trade paperback."),
            ]
        ),
    ),
    SettingSpec(
        key="margin_preset",
        label="Margins",
        description="Choose margin spacing for print layout.",
        default="standard",
        category="print",
        choices=_choices(
            [
                ("standard", "Standard", "Balanced book margins."),
                ("compact", "Compact", "Smaller margins to fit more text."),
                ("wide", "Wide", "More generous margins."),
                ("large-print", "Large print", "Larger margins and easier reading."),
            ]
        ),
    ),
    SettingSpec(
        key="create_imposed_pdf",
        label="Create imposed PDF",
        description="Also create a signature/imposed PDF for bookbinding.",
        default=False,
        category="binding",
        advanced=True,
        choices=_choices(
            [
                ("false", "No", "Do not create an imposed PDF."),
                ("true", "Yes", "Create an imposed PDF for binding."),
            ]
        ),
    ),
    SettingSpec(
        key="imposed_pages_per_signature",
        label="Pages per signature",
        description="Number of pages per folded signature. Must be a multiple of 4.",
        default=16,
        category="binding",
        advanced=True,
        choices=_choices(
            [
                ("8", "8 pages", "Two physical sheets per signature."),
                ("16", "16 pages", "Four physical sheets per signature."),
                ("24", "24 pages", "Six physical sheets per signature."),
                ("32", "32 pages", "Eight physical sheets per signature."),
            ]
        ),
    ),
    SettingSpec(
        key="binding_direction",
        label="Binding direction",
        description="Controls left-to-right or right-to-left imposition order.",
        default="ltr",
        category="binding",
        advanced=True,
        choices=_choices(
            [
                ("ltr", "Left-to-right", "Western-style binding direction."),
                ("rtl", "Right-to-left", "Mirrored binding direction."),
            ]
        ),
    ),
)


def settings_catalog(*, include_advanced: bool = True) -> list[dict[str, Any]]:
    specs = WEB_SAFE_SETTINGS if include_advanced else tuple(
        spec for spec in WEB_SAFE_SETTINGS if not spec.advanced
    )
    return [spec.to_dict() for spec in specs]


def settings_defaults(*, include_advanced: bool = True) -> dict[str, Any]:
    specs = WEB_SAFE_SETTINGS if include_advanced else tuple(
        spec for spec in WEB_SAFE_SETTINGS if not spec.advanced
    )
    return {spec.key: spec.default for spec in specs}


def validate_web_settings(settings: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize settings intended for future web forms."""

    specs = {spec.key: spec for spec in WEB_SAFE_SETTINGS}
    normalized = settings_defaults(include_advanced=True)

    unknown = sorted(set(settings) - set(specs))
    if unknown:
        raise ValueError(f"Unknown setting(s): {', '.join(unknown)}")

    for key, value in settings.items():
        spec = specs[key]

        if spec.choices:
            allowed = {choice.value for choice in spec.choices}
            normalized_value = str(value).lower() if isinstance(value, bool) else str(value)
            if normalized_value not in allowed:
                raise ValueError(
                    f"Invalid value for {key}: {value!r}. "
                    f"Expected one of: {', '.join(sorted(allowed))}"
                )

            if isinstance(spec.default, bool):
                normalized[key] = normalized_value == "true"
            elif isinstance(spec.default, int):
                normalized[key] = int(normalized_value)
            else:
                normalized[key] = normalized_value
        else:
            normalized[key] = value

    return normalized
