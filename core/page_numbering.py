from __future__ import annotations

from core.page_ornaments import page_ornament_counter_content

VALID_PAGE_NUMBER_START_MODES = {
    "after-title-page",
    "main-text",
    "first-page",
    "none",
}

VALID_FRONT_MATTER_NUMBER_STYLES = {
    "hidden",
    "roman-lower",
    "roman-upper",
    "arabic",
}

DEFAULT_PAGE_NUMBER_START_MODE = "after-title-page"
DEFAULT_FRONT_MATTER_NUMBER_STYLE = "hidden"


def normalize_page_number_start_mode(value: str | None) -> str:
    mode = (value or DEFAULT_PAGE_NUMBER_START_MODE).strip().lower()
    if mode not in VALID_PAGE_NUMBER_START_MODES:
        raise ValueError(
            f"Unknown page number start mode: {value!r}. "
            f"Expected one of: {', '.join(sorted(VALID_PAGE_NUMBER_START_MODES))}"
        )
    return mode


def normalize_front_matter_number_style(value: str | None) -> str:
    style = (value or DEFAULT_FRONT_MATTER_NUMBER_STYLE).strip().lower()
    if style not in VALID_FRONT_MATTER_NUMBER_STYLES:
        raise ValueError(
            f"Unknown front matter number style: {value!r}. "
            f"Expected one of: {', '.join(sorted(VALID_FRONT_MATTER_NUMBER_STYLES))}"
        )
    return style


def _front_matter_counter_content(style: str | None, ornament_key: str | None = None, ornament_amount: str | None = 'subtle') -> str:
    style = normalize_front_matter_number_style(style)
    if style == "roman-lower":
        return page_ornament_counter_content("counter(page, lower-roman)", ornament_key, ornament_amount)
    if style == "roman-upper":
        return page_ornament_counter_content("counter(page, upper-roman)", ornament_key, ornament_amount)
    if style == "arabic":
        return page_ornament_counter_content("counter(page)", ornament_key, ornament_amount)
    return "none"


def build_page_number_css(
    mode: str | None,
    front_matter_style: str | None = DEFAULT_FRONT_MATTER_NUMBER_STYLE,
    page_ornament: str | None = "none",
    page_ornament_amount: str | None = "subtle",
) -> str:
    mode = normalize_page_number_start_mode(mode)
    front_content = _front_matter_counter_content(front_matter_style, page_ornament, page_ornament_amount)
    main_content = page_ornament_counter_content("counter(page)", page_ornament, page_ornament_amount)

    if mode == "first-page":
        return f"""
/* Page numbering: show from first page. */
@page {{
  @bottom-center {{
    content: {main_content};
  }}
}}
"""

    if mode == "none":
        return """
/* Page numbering: disabled. */
@page {
  @bottom-center {
    content: none;
  }
}
"""

    if mode == "main-text":
        return f"""
/* Page numbering: front matter optional, main text restarts at 1. */
.title-page {{
  page: chapterfold-titlepage;
}}

.chapter {{
  page: chapterfold-frontmatter;
}}

.first-body-chapter,
.first-body-chapter ~ .chapter {{
  page: chapterfold-maintext;
}}

.first-body-chapter {{
  counter-reset: page 1;
}}

@page chapterfold-titlepage {{
  @bottom-center {{
    content: none;
  }}
}}

@page chapterfold-frontmatter {{
  @bottom-center {{
    content: {front_content};
  }}
}}

@page chapterfold-maintext {{
  @bottom-center {{
    content: {main_content};
  }}
}}
"""

    return f"""
/* Page numbering: suppress title page only. */
.title-page {{
  page: chapterfold-titlepage;
}}

@page {{
  @bottom-center {{
    content: {main_content};
  }}
}}

@page chapterfold-titlepage {{
  @bottom-center {{
    content: none;
  }}
}}
"""
