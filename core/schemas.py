
"""Shared data structures for ChapterFOLD jobs.

These classes are deliberately independent from PySide/GUI code so the same
contract can be used by the desktop app, CLI, tests, and future API backend.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4


@dataclass
class ChapterfoldSettings:
    """Shared conversion settings for ChapterFOLD.

    The field names intentionally include both legacy desktop/test names and
    future web/CLI names so this schema remains backwards-compatible while the
    app is refactored.
    """

    variant: str = "standard"
    export_docx: bool = False
    export_markdown: bool = False
    generate_clean_pdf: bool = True
    paragraph_spacing_mode: str = "traditional"
    contents_mode: str = "rebuild"
    page_number_start_mode: str = "after-title-page"
    front_matter_page_number_style: str = "hidden"
    page_ornament: str = "none"
    page_ornament_amount: str = "subtle"
    chapter_ornament: str = "none"

    page_size_preset: str = "default-trade"
    custom_trim_width_cm: Optional[float] = None
    custom_trim_height_cm: Optional[float] = None

    margin_preset: str = "standard"
    custom_margin_top_cm: Optional[float] = None
    custom_margin_bottom_cm: Optional[float] = None
    custom_margin_inside_cm: Optional[float] = None
    custom_margin_outside_cm: Optional[float] = None

    # Legacy/foundation field used by existing tests.
    signature_size: int = 16

    # Web/CLI-friendly imposition fields.
    create_imposed_pdf: bool = False
    imposed_pages_per_signature: Optional[int] = None
    binding_direction: str = "ltr"
    max_end_padding: Optional[int] = None

    def __post_init__(self) -> None:
        if self.imposed_pages_per_signature is None:
            self.imposed_pages_per_signature = self.signature_size
        else:
            self.signature_size = int(self.imposed_pages_per_signature)

    def validate(self) -> None:
        allowed_variants = {"standard", "aggressive-cleanup", "paragraph-dialogue-merge"}
        if self.variant not in allowed_variants:
            raise ValueError(f"Unknown variant: {self.variant}")

        allowed_contents_modes = {"keep", "remove", "rebuild", "rebuild-paged"}
        if self.contents_mode not in allowed_contents_modes:
            raise ValueError(f"Unknown contents_mode: {self.contents_mode}")

        allowed_page_number_start_modes = {"after-title-page", "main-text", "first-page", "none"}
        if self.page_number_start_mode not in allowed_page_number_start_modes:
            raise ValueError(f"Unknown page_number_start_mode: {self.page_number_start_mode}")

        allowed_front_matter_page_number_styles = {"hidden", "roman-lower", "roman-upper", "arabic"}
        if self.front_matter_page_number_style not in allowed_front_matter_page_number_styles:
            raise ValueError(f"Unknown front_matter_page_number_style: {self.front_matter_page_number_style}")

        allowed_page_ornaments = {'none', 'classic-rule', 'botanical-leaf', 'floral-corner', 'gothic-flourish', 'storybook', 'vine', 'laurel', 'victorian-dots', 'celestial', 'rose', 'ivy', 'acanthus', 'minimal-divider', 'poetic-vine', 'moon-garden', 'rose-window', 'ivy-thorn', 'asterism', 'bookbinder-rule'}
        if self.page_ornament not in allowed_page_ornaments:
            raise ValueError(f"Unknown page_ornament: {self.page_ornament}")

        allowed_page_ornament_amounts = {"subtle", "balanced", "ornate"}
        if self.page_ornament_amount not in allowed_page_ornament_amounts:
            raise ValueError(f"Unknown page_ornament_amount: {self.page_ornament_amount}")

        allowed_chapter_ornaments = {
            "none",
            "classic-rule",
            "botanical-divider",
            "poetic-vine",
            "moon-garden",
            "rose-window",
            "bookbinder-rule",
        }
        if self.chapter_ornament not in allowed_chapter_ornaments:
            raise ValueError(f"Unknown chapter_ornament: {self.chapter_ornament}")

        if self.signature_size <= 0:
            raise ValueError("signature_size must be positive.")
        if self.signature_size % 4 != 0:
            raise ValueError("signature_size must be divisible by 4.")

        if self.imposed_pages_per_signature is None:
            self.imposed_pages_per_signature = self.signature_size
        if int(self.imposed_pages_per_signature) <= 0:
            raise ValueError("imposed_pages_per_signature must be positive.")
        if int(self.imposed_pages_per_signature) % 4 != 0:
            raise ValueError("imposed_pages_per_signature must be divisible by 4.")

        if self.binding_direction not in {"ltr", "rtl"}:
            raise ValueError("binding_direction must be 'ltr' or 'rtl'.")

        if self.max_end_padding is not None and self.max_end_padding < 0:
            raise ValueError("max_end_padding must be zero or positive.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "ChapterfoldSettings":
        if data is None:
            return cls()
        known = {f.name for f in fields(cls)}
        unknown = sorted(set(data) - known)
        if unknown:
            raise ValueError(f"Unknown ChapterFOLD setting(s): {', '.join(unknown)}")
        return cls(**dict(data))


@dataclass
class ChapterfoldJobInput:
    input_epub: Path
    output_dir: Path
    settings: ChapterfoldSettings = field(default_factory=ChapterfoldSettings)
    job_id: str = field(default_factory=lambda: uuid4().hex)

    def __post_init__(self) -> None:
        self.input_epub = Path(self.input_epub)
        self.output_dir = Path(self.output_dir)
        if isinstance(self.settings, dict):
            self.settings = ChapterfoldSettings.from_dict(self.settings)

    def validate(self) -> None:
        self.settings.validate()
        if self.input_epub.suffix.lower() != ".epub":
            raise ValueError("Input file must be a .epub file.")
        if not self.input_epub.exists():
            raise FileNotFoundError(f"Input EPUB does not exist: {self.input_epub}")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_epub": str(self.input_epub),
            "output_dir": str(self.output_dir),
            "settings": self.settings.to_dict(),
            "job_id": self.job_id,
        }


@dataclass
class ChapterfoldJobResult:
    success: bool
    output_files: list[Path] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    error: Optional[str] = None
    stage: str = "unknown"
    job_id: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "output_files": [str(p) for p in self.output_files],
            "warnings": list(self.warnings),
            "error": self.error,
            "stage": self.stage,
            "job_id": self.job_id,
        }
