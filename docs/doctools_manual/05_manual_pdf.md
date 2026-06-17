# manual_pdf Module

## Overview

The `manual_pdf` module compiles modular PSAIR manual sections into a single
PDF document.

It performs the final stage of the documentation build workflow by:

1. Collecting Markdown manual files
2. Assembling them into one Markdown document
3. Invoking Pandoc to generate a PDF

This lets manuals stay modular and repository-friendly while still producing a
compiled manual suitable for distribution, publication, and archival
documentation.

PSAIR is currently alpha software. The documentation/manual tooling described
here is the supported part of the package; broader areas such as EDA, NLP, ETL,
and pipeline scaffolding remain experimental.

---

## Runtime Requirements

PDF compilation depends on external rendering tools:

- `pandoc`, the document converter
- a LaTeX PDF engine, usually `xelatex`

The Python package `pypandoc` is included in PSAIR's documentation dependency
group so PSAIR can discover Pandoc when `pypandoc` knows where it is. However,
installing `pypandoc` by itself does not always install the `pandoc.exe`
program. If `psair pdf` reports that Pandoc is missing, install Pandoc using one
of the setup options below.

---

## Setting Up Pandoc on Windows

### Option 1: Install Pandoc in the Conda environment

This is the simplest option when working inside the `psair` Conda environment:

```powershell
conda activate psair
conda install -c conda-forge pandoc
```

Then verify:

```powershell
pandoc --version
where pandoc
```

Because Conda installs Pandoc inside the active environment, this avoids editing
the global Windows PATH.

### Option 2: Install Pandoc with winget

From PowerShell:

```powershell
winget install JohnMacFarlane.Pandoc
```

Close and reopen the terminal, then verify:

```powershell
pandoc --version
where pandoc
```

The installer commonly places Pandoc under:

```text
C:\Program Files\Pandoc
```

If `pandoc --version` still fails after reopening the terminal, add that folder
to PATH manually.

### Option 3: Add Pandoc to PATH manually

Use this when Pandoc is installed but Windows cannot find it.

1. Open the Start menu and search for `Environment Variables`.
2. Open `Edit environment variables for your account`.
3. Select the user variable named `Path`.
4. Choose `Edit`.
5. Add the folder containing `pandoc.exe`, for example:

```text
C:\Program Files\Pandoc
```

6. Save the dialogs.
7. Close and reopen PowerShell or Command Prompt.
8. Run:

```powershell
pandoc --version
where pandoc
```

For a temporary PowerShell-only PATH update, use:

```powershell
$env:Path += ";C:\Program Files\Pandoc"
```

That lasts only for the current terminal session.

### Option 4: Download Pandoc through pypandoc

If `pypandoc` is installed, it can download a Pandoc binary:

```powershell
python -c "import pypandoc; pypandoc.download_pandoc()"
```

PSAIR will first look for `pandoc` on PATH. If it is not found and the requested
executable is the default `pandoc`, PSAIR will also ask `pypandoc` for its
Pandoc path.

This means `psair pdf` may work even when `where pandoc` cannot find anything.
To check the `pypandoc` path directly:

```powershell
python -c "import pypandoc; print(pypandoc.get_pandoc_path())"
```

On Windows, `pypandoc.download_pandoc()` commonly installs Pandoc under:

```text
C:\Users\<you>\AppData\Local\Pandoc
```

If you want Pandoc available to every terminal command, add that folder to PATH
using the manual PATH steps above.

---

## Setting Up a PDF Engine

Pandoc still needs a PDF engine such as `xelatex`.

Common Windows options include:

- MiKTeX
- TeX Live
- TinyTeX

After installation, verify:

```powershell
xelatex --version
where xelatex
```

The PSAIR CLI uses `xelatex` by default. You can choose another Pandoc-supported
engine with:

```powershell
psair pdf docs/doctools_manual --pdf-engine lualatex
```

---

## CLI Usage

Compile the doctools manual:

```powershell
psair pdf docs/doctools_manual
```

Useful options:

```powershell
psair pdf docs/doctools_manual --output docs/doctools_manual.pdf
psair pdf docs/doctools_manual --yaml docs/doctools_manual/manual_pdf.yaml
psair pdf docs/doctools_manual --margin 0.8in
psair pdf docs/doctools_manual --toc-depth 3
psair pdf docs/doctools_manual --include-outline
psair pdf docs/doctools_manual --file-dividers
psair pdf docs/doctools_manual --keep-temp-md
```

Before building the PDF, the CLI can prepare the manual outline and run
character/content checks. If issues are found, interactive runs ask whether to
continue. For automated workflows:

```powershell
psair pdf docs/doctools_manual --non-interactive --force
```

---

## Core Function

## build_manual_pdf

Primary entry point for PDF compilation.

```python
build_manual_pdf(manual_dir)
```

### Purpose

Creates a compiled manual PDF from modular Markdown files.

### Parameters

| Parameter | Description |
|----------|-------------|
| `manual_dir` | Root manual directory |
| `yaml_path` | Optional Pandoc metadata YAML |
| `output_path` | Destination PDF file |
| `pandoc` | Pandoc executable name or path |
| `pdf_engine` | Pandoc PDF engine |
| `pagebreaks` | Insert page breaks between sections |
| `strip_heading_numbers` | Remove numeric prefixes from headings |
| `include_outline` | Include `00_outline.md` in the PDF |
| `include_exts` | File extensions to include |
| `file_dividers` | Insert HTML comments marking file boundaries |
| `extra_pandoc_args` | Additional Pandoc CLI arguments |
| `keep_temp_md` | Preserve the assembled Markdown file |
| `temp_md_path` | Explicit path for assembled Markdown |
| `margin` | Page margin override |
| `toc` | Enable automatic table of contents |
| `toc_depth` | Maximum table-of-contents heading depth |

### Workflow

The function performs the following sequence:

1. Discover Markdown files
2. Assemble them into a unified Markdown document
3. Write a temporary Markdown file
4. Invoke Pandoc to generate the PDF
5. Remove temporary artifacts unless preservation is requested

Returns a `Path` representing the compiled PDF location.

---

## Composed Manual Exports

For webapp downloads and multi-source manuals, PSAIR can compose manual roots
first and then export the resulting virtual tree. The helper
`build_composed_manual_markdown()` in `psair.webapp.manual_export` accepts the
same source concept used by the Streamlit viewer:

```python
from psair.examples import ManualSource
from psair.webapp.manual_export import build_composed_manual_markdown

markdown_text, section_meta = build_composed_manual_markdown(
    [
        ManualSource("docs/manual", name="manual", role="authored"),
        ManualSource(
            "src/project/examples/assets/rendered_docs/example_io",
            name="example_io",
            source_manual="generated_example_io",
            role="generated",
        ),
    ],
    infer_from_paths=True,
)
```

The returned Markdown uses the same virtual ordering as the composed viewer.
For example, generated `example_io` command views can export after authored
`01_quickstart.md`, `02_usage_guide.md`, and `04_implementation_notes.md` as a
virtual `05_example_io.md` section. YAML front matter is stripped before export.
See Manual Composition (`docs/doctools_manual/09_manual_composition.md`) for
the full source, metadata, virtual-path, and limitation contract.

---

## Supporting Utilities

## iter_markdown_files

Collects Markdown manual files from the manual directory.

Key behaviors:

- recursive directory scanning
- hidden path exclusion
- deterministic ordering
- optional exclusion of `00_outline.md`

Example discovered structure:

```text
manual/
    01_intro.md
    02_installation.md
    03_workflow/
        03_01_overview.md
```

## assemble_markdown

Combines multiple Markdown files into a single document.

Example behavior:

```text
Section 1 text

\newpage

Section 2 text
```

Optional features include:

- page breaks between sections
- removal of numeric heading prefixes
- file boundary comments

## strip_leading_heading_numbers

Removes numeric prefixes from Markdown headings.

Example:

```markdown
# 03 Overview
```

becomes:

```markdown
# Overview
```

## add_pagebreaks_between_sections

Inserts LaTeX page breaks between assembled Markdown sections:

```markdown
\newpage
```

Pandoc interprets these directives during PDF generation.

## build_pandoc_extra_args

Constructs Pandoc CLI arguments used during compilation.

Example generated arguments:

```text
--toc
--toc-depth 3
-V geometry:margin=1in
```

## run_pandoc

Executes the Pandoc command used to produce the final PDF.

Example command executed internally:

```powershell
pandoc assembled.md -o manual.pdf --pdf-engine xelatex
```

The function captures output and raises a descriptive error if compilation
fails.

## resolve_executable

Resolves the Pandoc executable from PATH. For the default `pandoc` executable,
PSAIR can also ask `pypandoc` for a known Pandoc path.

If Pandoc is not found, the function raises a setup-oriented error message.

---

## Troubleshooting

If PSAIR cannot find Pandoc:

```powershell
where pandoc
pandoc --version
```

If Pandoc is present but PDF compilation fails with a LaTeX error:

```powershell
where xelatex
xelatex --version
```

If MiKTeX reports that this is a fresh TeX installation, open the MiKTeX Console
once and finish the first-run setup. If prompted, allow MiKTeX to install
missing packages automatically. Then reopen the terminal and retry the PSAIR PDF
command.

If Pandoc was installed into a different Conda environment, activate the same
environment used to run PSAIR:

```powershell
conda activate psair
python -m pip show psair
where psair
where pandoc
```

---

## Summary

`manual_pdf` compiles modular Markdown manuals into a formatted PDF.

Core capabilities include:

- Markdown file discovery
- section assembly
- optional formatting transformations
- Pandoc-driven PDF compilation
- PATH and `pypandoc` discovery for the Pandoc executable

This module completes PSAIR's supported documentation workflow by producing
publishable manuals from modular source files.
