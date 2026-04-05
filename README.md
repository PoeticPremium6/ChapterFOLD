````md
# ChapterFOLD

<p align="center">
  <img src="docs/icon.png" alt="ChapterFOLD logo" width="120" />
</p>

<p align="center">
  Convert EPUBs into cleaner, print-ready PDF and DOCX interiors for bookbinding and personal printing.
</p>

## Windows download

For normal use, you do **not** need Python.

1. Download the latest Windows release ZIP from the Releases page
2. Extract the ZIP fully
3. Open the extracted folder
4. Run `ChapterFOLD.exe`

## What ChapterFOLD does

ChapterFOLD is a Windows-first tool for turning EPUB books into cleaner, more practical outputs for printing, editing, and bookbinding.

It currently supports:

- EPUB to interior PDF
- EPUB to editable DOCX
- multiple cleanup modes for dialogue and paragraph issues
- paragraph spacing modes
- margin presets
- baseline comparison against standard cleanup
- text cleanup preview in the desktop app
- print-friendly output naming and layout controls

## Who it is for

ChapterFOLD is especially useful for:

- hobby bookbinders
- readers making personal physical copies
- fanfiction readers exporting EPUBs into printable interiors
- people who want more control over spacing, margins, and layout

## Main desktop app features

The desktop app lets you:

- choose an input EPUB
- choose an output folder
- select a cleanup mode
- select a paragraph spacing mode
- select a margin preset
- optionally export DOCX
- compare results against a standard baseline
- preview text cleanup changes
- open the generated output files directly

## Cleanup modes

- **Standard Cleanup** — light cleanup for common EPUB formatting issues
- **Dialogue Merge** — better at merging dialogue split across paragraph boundaries
- **Aggressive Cleanup** — stronger cleanup heuristics for awkward spacing and broken dialogue continuity

## Paragraph spacing modes

- **Traditional** — paragraph spacing with indents
- **No indents** — keep paragraph spacing, remove indents
- **Indented compact** — minimal paragraph gap with indents
- **Uniform** — no extra paragraph gap and no indents

## Margin presets

- **Standard**
- **Compact**
- **Wide**
- **Large print friendly**

## Example desktop app view

![ChapterFOLD desktop app](docs/ChatperFOLD_Example.PNG)

## Running from source

These steps are only for developers or contributors working from the repository source code.

### Install dependencies

From the repo root:

```bash
pip install -r requirements.txt
pip install -r chapterfold_app/requirements.txt
````

### Run the desktop app

```bash
cd chapterfold_app
py app.py
```

## Building the Windows executable

From `chapterfold_app`:

```powershell
pyinstaller --noconfirm --windowed --name ChapterFOLD --icon assets\icon.ico --paths .. app.py
```

The built Windows app will appear under:

```text
chapterfold_app\dist\ChapterFOLD\
```

When sharing the app, distribute the **entire** `dist\ChapterFOLD\` folder or a ZIP of that folder.

## Script workflow

The repository also includes the earlier script-based workflow.

### Generate output variants

```bash
py Scripts/generate_variants.py "C:\path\to\book.epub"
```

### Test cleanup samples

```bash
py Scripts/test_cleanup_samples.py
```

Or with a sample file:

```bash
py Scripts/test_cleanup_samples.py Scripts\test_samples.txt
```

## Project structure

```text
ChapterFOLD/
├─ Archive/
├─ Scripts/
├─ chapterfold_app/
│  ├─ app.py
│  ├─ assets/
│  ├─ gui/
│  ├─ services/
│  └─ requirements.txt
├─ core/
├─ docs/
├─ tests/
├─ requirements.txt
└─ README.md
```

## Notes for Windows users

If you are running from source rather than using the packaged release, WeasyPrint may require native Windows libraries to be available.

In some environments, this may require setting:

```powershell
$env:WEASYPRINT_DLL_DIRECTORIES="C:\msys64\ucrt64\bin"
```

before running the app or scripts.

Release users should not need to do this if the packaged app has been bundled correctly.

## Feedback wanted

Feedback is especially useful on:

* badly formatted EPUBs
* dialogue-heavy books
* odd paragraph spacing cases
* fanfiction EPUB exports
* margin and spacing preferences
* Windows packaging and usability issues

If you test the app, it is especially helpful to report:

* whether it launched successfully
* what EPUB you tested
* which cleanup mode you used
* whether the output looked better or worse
* any broken dialogue, spacing, or pagination issues

## Status

ChapterFOLD is currently an active early-stage project.

The desktop app is usable, but still evolving. Expect changes to cleanup heuristics, UI wording, output options, and packaging as more books and edge cases are tested.

## License

remium6/ChapterFOLD "GitHub - PoeticPremium6/ChapterFOLD: Python UI to process open-access EPUB files into formats suitable for bookbinders · GitHub"
