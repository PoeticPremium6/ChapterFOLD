def build_css(settings: LayoutSettings) -> str:
    mode = (settings.paragraph_spacing_mode or "traditional").strip().lower()

    if mode == "uniform":
        paragraph_css = """
p {
  margin: 0;
  text-align: justify;
  text-indent: 0;
  orphans: 2;
  widows: 2;
}

.chapter p + p {
  text-indent: 0;
  margin-top: 0;
}
"""
    elif mode == "no-indents":
        paragraph_css = """
p {
  margin: 0 0 0.65em 0;
  text-align: justify;
  text-indent: 0;
  orphans: 2;
  widows: 2;
}

.chapter p + p {
  text-indent: 0;
}
"""
    else:
        paragraph_css = """
p {
  margin: 0 0 0.65em 0;
  text-align: justify;
  text-indent: 0;
  orphans: 2;
  widows: 2;
}

.chapter p + p {
  text-indent: 1.2em;
}
"""

    return f"""
@page {{
  size: {cm(settings.trim_width_cm)} {cm(settings.trim_height_cm)};
  margin-top: {cm(settings.margin_top_cm)};
  margin-bottom: {cm(settings.margin_bottom_cm)};
  @bottom-center {{
    content: counter(page);
    font-size: 9pt;
  }}
}}

@page :right {{
  margin-left: {cm(settings.margin_inside_cm)};
  margin-right: {cm(settings.margin_outside_cm)};
}}

@page :left {{
  margin-left: {cm(settings.margin_outside_cm)};
  margin-right: {cm(settings.margin_inside_cm)};
}}

html {{
  font-size: {settings.font_size_pt}pt;
}}

body {{
  margin: 0;
  padding: 0;
  color: #111;
  font-family: {settings.font_family};
  line-height: {settings.line_height};
  -weasy-bookmark-level: none;
}}

.title-page {{
  break-after: page;
  min-height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
}}

.title-wrap h1 {{
  margin: 0 0 0.45em 0;
  font-size: {settings.font_size_pt * 2.0:.2f}pt;
  line-height: 1.15;
}}

.title-wrap .author {{
  margin: 0;
  font-size: {settings.font_size_pt * 1.15:.2f}pt;
}}

.blank-page {{
  break-after: page;
}}

.first-body-chapter {{
  break-before: right;
}}

.chapter {{
  break-before: page;
}}

.first-body-chapter.chapter {{
  break-before: right;
}}

.chapter-title {{
  text-align: center;
  margin: 0 0 1.8em 0;
  font-size: {settings.font_size_pt * 1.45:.2f}pt;
  page-break-after: avoid;
}}

{paragraph_css}

h1, h2, h3, h4 {{
  page-break-after: avoid;
}}

em {{
  font-style: italic;
}}

strong {{
  font-weight: bold;
}}

hr, .scene-break {{
  margin: 1.2em auto;
  width: 25%;
  border: 0;
  border-top: 1px solid #666;
}}
"""
