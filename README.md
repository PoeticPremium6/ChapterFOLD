# ChapterFOLD

Convert EPUB books into binder-ready PDFs with custom margins, title pages, page numbering, and 16-page signature imposition.

## Overview

Chapterfold is a small Python toolchain for turning EPUBs into clean, printable book interiors for physical bookbinding.

It is designed for hobby binders, fanfiction readers, and makers who want to take a digital text and produce a PDF that is easier to print, fold, gather, and bind.

The current workflow is:

1. Take an EPUB as input
2. Generate a formatted interior PDF
3. Impose that PDF into printer spreads for 16-page signatures

## Features

- EPUB to print-ready interior PDF
- Custom trim size
- Mirrored margins for binding
- Bottom-centre page numbering
- Title page followed by a blank page
- Body starts on a right-hand page
- Adjustable font family and font size
- 16-page signature imposition by default
- Optional limit on blank pages added to fill the final signature
- Output files written into an organized output folder

## Current Scripts

### `epub_to_pdf.py`

Creates a formatted interior PDF from an EPUB.

By default it:
- reads title and author from EPUB metadata
- creates a title page
- inserts a blank page after the title page
- starts the main text on a recto page
- applies bookbinding-friendly mirrored margins
- numbers pages at the bottom centre
- writes the output to a new folder next to the EPUB

Example output structure:

```text
Running_on_Air.epub
Running_on_Air_output/
  interior.pdf
