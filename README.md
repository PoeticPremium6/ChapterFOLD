````markdown
# ChapterFOLD

Convert EPUB books into binder-ready PDFs with custom margins, title pages, page numbering, and signature imposition for physical bookbinding.

## Overview

ChapterFOLD is a small Python toolchain I started building to help turn EPUBs into something much more practical for hand bookbinding.

A lot of tools out there are either made for ebooks, generic PDF editing, or print imposition on its own. I wanted something that sits in the middle: a way to take a digital book, cleanly format it into a printable interior, and then impose it into signatures that are actually useful for binding.

At the moment, the workflow is simple:

1. Take an EPUB as input  
2. Generate a formatted interior PDF  
3. Impose that PDF into printer spreads for folded signatures  

This project is especially aimed at:
- hobby binders
- fanfiction readers who want personal physical copies
- makers who enjoy turning digital texts into real books

## What the code does

Right now, the project has two main parts.

### 1. EPUB to interior PDF

This step takes an EPUB and turns it into a cleaner, more bookbinding-friendly PDF.

It currently:
- reads title and author metadata from the EPUB
- creates a title page
- inserts a blank page after the title page
- starts the main text on a right-hand page
- applies mirrored margins for binding
- adds page numbers at the bottom centre
- writes the output into a dedicated folder next to the original EPUB

### 2. Interior PDF to imposed signature PDF

This step takes the interior PDF and rearranges the pages into printable spreads.

It currently:
- supports folded signatures
- defaults to **4 sheets per signature**
- which means **16 book pages per signature**
- adds blank pages only at the end if needed
- lets you limit how many blank pages are allowed
- writes the imposed PDF into the same output folder

## Features

- EPUB to print-ready interior PDF
- Custom trim size
- Mirrored margins for binding
- Bottom-centre page numbering
- Title page followed by a blank page
- Body starts on a right-hand page
- Adjustable font family and font size
- Signature imposition for folded bookbinding
- Default setup of **4 sheets / 16 pages per signature**
- Optional limit on blank pages added to fill the last signature
- Output files written into an organized output folder

## Project structure

```text
ChapterFOLD/
  core/
    __init__.py
    epub_service.py
    impose_service.py
  scripts/
    __init__.py
    epub_to_pdf.py
    impose_signatures.py
  requirements.txt
  README.md
````

## Requirements

* Python 3.10+
* WeasyPrint system dependencies installed correctly
* A working Python virtual environment is strongly recommended

Python packages used:

* `beautifulsoup4`
* `ebooklib`
* `lxml`
* `weasyprint`
* `pypdf`

## Install

From the repo root:

```bash
pip install -r requirements.txt
```

## Windows note

If you are on Windows, `WeasyPrint` may need extra native libraries installed before EPUB-to-PDF conversion works correctly.

In my setup, I also needed to set:

```powershell
$env:WEASYPRINT_DLL_DIRECTORIES="C:\msys64\ucrt64\bin"
```

before running the EPUB conversion script.

## How to run it locally

### Step 1: convert EPUB to interior PDF

From the repo root:

```powershell
python scripts\epub_to_pdf.py "C:\path\to\your\book.epub"
```

If the script succeeds, it will create a folder next to the EPUB and place the PDF there.

For example:

```text
Running_on_Air.epub
Running_on_Air_output/
  interior.pdf
```

A successful run will print something like:

```text
EPUB to PDF completed successfully.
Input EPUB:       C:\Running_on_Air.epub
Detected title:   Running on Air
Detected author:  eleventy7
Used title:       Running on Air
Used author:      eleventy7
Output folder:    C:\unning_on_Air_output
Output PDF:       C:\interior.pdf
```

### Step 2: impose the PDF into signatures

Once `interior.pdf` exists, run:

```powershell
python scripts\impose_signatures.py "C:\path\to\your\book_output\interior.pdf"
```

That should create something like:

```text
Running_on_Air_output/
  interior.pdf
  imposed_4sheets_16pages.pdf
```

A successful run will print something like:

```text
Signature imposition completed successfully.
Input PDF:            C:\interior.pdf
Output folder:        C:\Running_on_Air_output
Output PDF:           C:\imposed_4sheets_16pages.pdf
Input pages:          320
Sheets/signature:     4
Pages/signature:      16
End blanks added:     0
Output sheet sides:   160
Physical sheets/sig:  4
```

## Common usage examples

### Basic EPUB conversion

```powershell
python scripts\epub_to_pdf.py "C:\unning_on_Air.epub"
```

### Override title and author

```powershell
python scripts\epub_to_pdf.py "C:\Running_on_Air.epub" --title "Running on Air" --author "eleventy7"
```

### Set a custom output path

```powershell
python scripts\epub_to_pdf.py "C:\Running_on_Air.epub" --out "C:\interior.pdf"
```

### Impose with default 4-sheet / 16-page signatures

```powershell
python scripts\impose_signatures.py "C:\Running_on_Air_output\interior.pdf"
```

### Explicitly choose sheets per signature

```powershell
python scripts\impose_signatures.py "C:\Running_on_Air_output\interior.pdf" --sheets-per-signature 4
```

### Refuse too much blank padding at the end

```powershell
python scripts\impose_signatures.py "C:\Running_on_Air_output\interior.pdf" --max-end-padding 8
```

## Current defaults

### Interior PDF defaults

* Trim size: `15.24 cm x 22.86 cm`
* Top margin: `1.5 cm`
* Bottom margin: `1.5 cm`
* Inside margin: `1.8 cm`
* Outside margin: `1.0 cm`
* Font size: `11.5 pt`
* Page numbers: bottom centre
* Font stack: Garamond-style fallback stack

### Signature defaults

* `4 sheets per signature`
* `16 pages per signature`

## Why I made this

I wanted something practical. Book-binding is a traditional artform, but it can use some help from modern technology. I wanted a way to take digital texts, especially EPUBs and fanfiction, and turn them into something I could realistically print, fold, gather, and sew without fighting several different tools along the way.


## Intended use

This project is meant for formatting books for personal use and bookbinding workflows.

Please respect authors, licenses, and platform rules when choosing what you convert and print.

## Contributing

This started as a personal project, but suggestions, issues, and improvements are welcome.

## License

The MIT License (MIT)
Copyright © 2026 PoeticPremium

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Fork this project to create your own MIT license that you can always link to.
```
```
